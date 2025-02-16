from typing import Dict, Any, List
import os
import pandas as pd
from core.transcriber import Transcriber, TranscriptionConfig
from utils.json_utils import extract_segments_info, format_transcription_to_text
from fastapi import HTTPException
import time

class TranscriptionService:
    def __init__(self, config: TranscriptionConfig):
        self.config = config
        self.transcriber = Transcriber(config)

    async def transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        """处理单个音频文件的转写请求"""
        if not os.path.exists(audio_path):
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        try:
            # 处理音频转写
            times = await self.process_audio_transcription(audio_path)
            
            # 获取输出文件路径
            filename = os.path.basename(audio_path)
            base_name = os.path.splitext(filename)[0]
            output_file = os.path.join("output", f"{base_name}.json")
            
            # 处理JSON并创建简化版本
            simplified_output_file = extract_segments_info(output_file)
            
            return {
                "status": "success",
                "message": "Transcription completed successfully",
                **times,
                "output_file": output_file,
                "simplified_output_file": simplified_output_file
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def process_single_file(self, title: str, file_path: str) -> Dict[str, bool]:
        """处理单个文件的下载和转写"""
        try:
            # 转写音频
            result = await self.transcription_service.transcribe_audio(file_path)
            
            # 将简化的JSON转换为文本格式
            simplified_json_path = result['simplified_output_file']
            txt_output_path = simplified_json_path.replace('.json', '.txt')
            format_transcription_to_text(simplified_json_path, txt_output_path)
            print(f"已生成文本文件: {txt_output_path}")
            
            # 转写成功后删除音频文件
            os.remove(file_path)
            print(f"已删除音频文件: {file_path}")
            
            # 更新TSV文件中的下载状态
            tsv_path = "./output/feed/feed.tsv"
            if os.path.exists(tsv_path):
                df = pd.read_csv(tsv_path, sep='\t', dtype={'isDownload': str, 'title': str})
                df.loc[df['title'] == title, 'isDownload'] = 'true'
                df.to_csv(tsv_path, sep='\t', index=False)
                print(f"已更新TSV文件中的下载状态: {title}")
            
            return {"success": True, "title": title}
        except Exception as e:
            print(f"处理文件 {title} 失败: {str(e)}")
            import traceback
            print(f"错误详情:\n{traceback.format_exc()}")
            return {"success": False, "title": title, "error": str(e)}

    async def batch_transcribe_downloaded_audio(self) -> Dict[str, List[str]]:
        """批量处理下载的音频文件"""
        audio_dir = "./output/feed/audio"
        tsv_path = "./output/feed/feed.tsv"

        if not os.path.exists(audio_dir):
            raise HTTPException(status_code=404, detail="Audio directory not found")

        if not os.path.exists(tsv_path):
            raise HTTPException(status_code=404, detail="Feed TSV file not found")

        success_files = []
        failed_files = []

        # 获取所有MP3文件
        audio_files = [f for f in os.listdir(audio_dir) if f.endswith('.mp3')]

        if not audio_files:
            print("没有找到需要转写的音频文件")
            return {"success": [], "failed": []}

        print(f"\n=== 开始批量转写 {len(audio_files)} 个文件 ===")

        # 读取TSV文件
        df = pd.read_csv(tsv_path, sep='\t', dtype={'isDownload': str, 'title': str})

        for index, audio_file in enumerate(audio_files, 1):
            audio_path = os.path.join(audio_dir, audio_file)
            title = os.path.splitext(audio_file)[0]  # 获取不带扩展名的文件名

            print(f"\n[{index}/{len(audio_files)}] 开始处理: {audio_file}")

            try:
                # 转写音频
                result = await self.transcribe_audio(audio_path)

                # 将简化的JSON转换为文本格式
                format_transcription_to_text(
                    result['simplified_output_file'],
                    result['simplified_output_file'].replace('.json', '.txt')
                )

                # 更新TSV文件中的状态
                matching_rows = df[df['title'].apply(lambda x: clean_filename(x)) == title]
                if not matching_rows.empty:
                    original_title = matching_rows.iloc[0]['title']
                    df.loc[df['title'] == original_title, 'isDownload'] = 'true'
                    df.to_csv(tsv_path, sep='\t', index=False)
                    print(f"已更新TSV文件中的状态: {original_title}")
                else:
                    print(f"警告: 在TSV文件中未找到标题: {title}")

                # 删除音频文件
                os.remove(audio_path)
                print(f"已删除音频文件: {audio_path}")

                success_files.append(title)
                print(f"处理完成: {result['simplified_output_file']}")

            except Exception as e:
                print(f"处理失败: {str(e)}")
                import traceback
                print(f"错误详情:\n{traceback.format_exc()}")
                failed_files.append(title)

        print(f"\n=== 批量转写完成 ===")
        print(f"成功: {len(success_files)} 个文件")
        print(f"失败: {len(failed_files)} 个文件")

        return {
            "success": success_files,
            "failed": failed_files
        }
    
    async def process_audio_transcription(self, audio_path: str) -> Dict[str, Any]:
        """处理音频转写的核心逻辑"""
        # 转写步骤
        print("\n=== 开始转写 ===")
        start_time = time.time()
        transcriptions = self.transcriber.transcribe(audio_path=audio_path)
        transcribe_time = time.time() - start_time
        print(f"转写耗时: {transcribe_time:.2f}秒")

        # 对齐步骤
        print("\n=== 开始对齐 ===")
        start_time = time.time()
        transcriptions = self.transcriber.align_transcriptions(transcriptions)
        align_time = time.time() - start_time
        print(f"对齐耗时: {align_time:.2f}秒")

        # 说话人分离步骤
        print("\n=== 开始分离说话人 ===")
        start_time = time.time()
        transcriptions = self.transcriber.diarize_transcriptions(transcriptions)
        diarize_time = time.time() - start_time
        print(f"分离耗时: {diarize_time:.2f}秒")

        # 写入步骤
        start_time = time.time()
        self.transcriber.write_transcriptions(transcriptions=transcriptions)
        write_time = time.time() - start_time

        # 计算总时间
        total_time = transcribe_time + align_time + diarize_time + write_time
        
        return {
            "transcribe_time": round(transcribe_time, 2),
            "align_time": round(align_time, 2),
            "diarize_time": round(diarize_time, 2),
            "write_time": round(write_time, 2),
            "total_time": round(total_time, 2)
        }