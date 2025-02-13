import torch

print("PyTorch version:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())
print("CUDA device count:", torch.cuda.device_count())
if torch.cuda.is_available():
    print("CUDA device name:", torch.cuda.get_device_name(0))
    print("CUDA version:", torch.version.cuda)
    
    # 测试 CUDA 计算
    x = torch.rand(5, 3)
    print("Tensor device (before):", x.device)
    x = x.cuda()
    print("Tensor device (after):", x.device) 