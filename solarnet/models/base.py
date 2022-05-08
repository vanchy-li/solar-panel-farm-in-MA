import torch
from torch import nn
from torchvision.models import resnet34


class ResnetBase(nn.Module):
    """ResNet pretrained on Imagenet. This serves as the
    base for the classifier, and subsequently the segmentation model

    Attributes:
        imagenet_base: boolean, default: True
            Whether or not to load weights pretrained on imagenet
    """
    def __init__(self, imagenet_base: bool = True) -> None:
        super().__init__()

        resnet = resnet34(pretrained=imagenet_base).float()
        resnet._modules['conv1'] = nn.Conv2d(12,64,kernel_size=(7,7),stride=(2,2),padding=(3,3),bias=False)
        self.pretrained = nn.Sequential(*list(resnet.children())[:-2])
        
        #resnet = nn.Sequential(*(list(resnet.children())[:-2]))#remove last two layers (avpool and fc)
        #self.resnet11c = resnet

    def forward(self, x):
        # Since this is just a base, forward() shouldn't directly
        # be called on it.
        raise NotImplementedError
