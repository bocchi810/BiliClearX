> [!Note]
> 此仓库为个人对 [BiliClear](https://github.com/qaqFei/BiliClear) 的后续维护
> 
> 本仓库会对原仓库的**部分** issues 进行实现
>
> 下次更新时间 **国庆**


# TODO
- [ ]  ~~`BiliClearX` 的 WebUI 重构 [#71](https://github.com/qaqFei/BiliClear/issues/71)~~ 太麻烦了，砍了
- [x] `BiliClearX` 的审核系统实现(此项会同时解决误判问题) [#62](https://github.com/qaqFei/BiliClear/issues/62) [#50](https://github.com/qaqFei/BiliClear/issues/50) [#66](https://github.com/qaqFei/BiliClear/issues/66) [#64](https://github.com/qaqFei/BiliClear/issues/64)
- [x] `BiliClearX` 指定举报人实现 [#38](https://github.com/qaqFei/BiliClear/issues/38)
- [x] `BiliClearX` 举报策略调整 [#??](#)
- [x] 支持较低版本的 Python ![Python Version](https://img.shields.io/badge/Python%20Version-%3E%3D3.10-blue)


![BiliClearX](https://socialify.git.ci/molanp/BiliClearX/image?description=1&descriptionEditable=Report%20violating%20Bilibili%20users%20in%20batches.&font=Jost&forks=1&issues=1&language=1&name=1&owner=1&pattern=Charlie%20Brown&pulls=1&stargazers=1&theme=Auto)

# BiliClearX

- `BiliClearX` 是一个可以批量举报B站不良信息的程序
- `BiliClearX`需使用 **Python 3.10 及以上版本**

## 使用方法
### 使用EXE文件
- 开始检查评论(此脚本可以一直挂到后台)
    - 双击运行`biliclearX.exe`(如果可以，请使用管理员权限)
    - 可以使用`--mode`参数指定模式
    - `--mode 1`: 检查全部视频
    - `--mode 2`: 检查指定视频
        - `--extra bivd`: 视频 bvid，不传入则需要手动输入
    - `--mode 3`: 检查指定用户
        - `--extra uid`: 用户 uid，不传入则需要手动输入
    - eg. `biliClearX.exe --mode 2 --extra bv1h44y1e7j7` 检查`bv1h44y1e7j7`下的评论
- 审查疑似违规评论
    - 双击运行`Review.exe`
### 直接运行代码
- `BiliClearX` 使用 `Python` 开发，使用 `pip` 安装依赖
```shell
pip install -r requirements.txt
```
- 开始检查评论(此脚本可以一直挂到后台)
    - `python biliclearX.py`
    - 可以使用`--mode`参数指定模式
    - `--mode 1`: 检查全部视频
    - `--mode 2`: 检查指定视频
        - `--extra bivd`: 视频 bvid，不传入则需要手动输入
    - `--mode 3`: 检查指定用户
        - `--extra uid`: 用户 uid，不传入则需要手动输入
    - eg. `python biliclearX.py --mode 2 --extra bv1h44y1e7j7` 检查`bv1h44y1e7j7`下的评论
- 审查疑似违规评论
    - `python Review.py`

## 鸣谢

- [BiliClear](https://github.com/qaqFei/BiliClear)
- [bilibili-API-collect](https://github.com/SocialSisterYi/bilibili-API-collect)

## 免责声明

`BiliClearX` 仅用于学习交流, 不可用于商业用途
使用 `BiliClearX` 造成的任何后果由用户自行承担, 开发者不对此负责, 请谨慎使用该工具


## License

[MIT License](LICENSE)
