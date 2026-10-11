# 视频/音频分析工具链(产物必须真读, 2026-09-13 补)

生成视频/音频后**不能只看 `status: success`**: 画面要抽帧后用 `read_image` 逐张看, 音频要转成文字/特征/频谱图后再判断。**AI 没有听觉, 唯一"看"的通道是 `read_image`(只认图)** ⇒ 视频/音频必须先落成帧图/频谱图。**完整链路、能力边界、已知坑与两个工具的完整源码见 `docs\视频音频分析工具链.md`**(源码以该文档为准,不再依赖已移除的临时目录)。

全链四步(全部离线, 实测样本 = 0043 关键帧视频):

1. **定位产物**: `GET /history?max_items=N` → `outputs.<node>.{images,videos,audio,gifs}[].{filename,type}`; `type: temp` → `ComfyUI\temp\`, `type: output` → `media\<项目>\`(真实数据勿删; 保存类节点还会再建一层子目录 —— 优先用工作流的 md 表文件名, 没有 md 表节点才用工作流名, `filename` 不带该层级, 需从插件返回消息确认); `history.prompt[<n>]` 是当时的 API 图(可查节点数/mdtable `selected.id`)。同名前缀的 temp 文件会累积, 只用 mtime 最新那个。
2. **探针**: `ffprobe -v error -print_format json -show_format -show_streams <文件>`; 核对视频 宽高/fps/总帧数、音频 采样率/声道/**有没有音轨**(H3 无音轨多为 `overall_soundscape` 段没写对)。`总帧数 ÷ fps = 时长`(H3 固定 24 fps: 362 帧 = 15.083s)。
3. **画面**: `ffmpeg -y -i in.mp4 -ss 11.000 -frames:v 1 f011.png`(精确; `-ss` 放 `-i` 之前 = 快但可能偏几帧) + 联络表 `-vf "fps=1/2,scale=640:-1,tile=4x3" -frames:v 1 grid.png` → `read_image` 判读: 锚点主体在不在、数量/位置对不对、有没有被文字描述替换掉(实测: 提示词写"摊开的手稿", 中段笔记本就变成了摊开的书)。
4. **音频**: `ffmpeg -y -i in.mp4 -ac 1 -ar 16000 mono16k.wav` → **SenseVoiceSmall**(`models\TTS\SenseVoiceSmall`, funasr 加载, 传本地路径 + `disable_update=True` ⇒ 不发网络请求) 出 `<|语种|><|情绪|><|事件|>文本`, 即 转写(中/英/日/韩/粤)/情感(HAPPY·SAD·ANGRY·NEUTRAL)/事件(Speech·BGM·Applause·Laughter 等); 声学特征用 librosa + pyloudnorm(响度 LUFS/节奏 BPM/频谱质心/谱平坦度/F0); 频谱图与波形图用 `ffmpeg -lavfi "showspectrumpic=s=1024x512"` / `"showwavespic=s=1024x256"` 落 PNG 后再 `read_image` 看。

能力边界(**别承诺做不到的**): 转写/情绪/事件/响度/节奏/结构 ✅; **性别**仅"有人声时按 F0 中位数"启发式(纯音乐无效, 实测把贝斯基频判成了男声) ⚠️; 音色只能客观化描述(低沉/明亮/沙哑), 不能"像谁" ⚠️; **说话人分离、认出具体曲目、认人、主观听感(自然不自然/口音) ❌**(缺声纹与 diarization 模型, 曲目识别需联网指纹库, 听感需人耳)。可升级项(faster-whisper 权重 / pyannote·3D-Speaker / CLAP·AST / chromaprint)见该文档 §7。

坑: ① 脚本报 `exit code 1` 常是 torch `pynvml` FutureWarning 走 stderr 被 PowerShell 当 `NativeCommandError`, 判成功看业务输出不看退出码; ② funasr 与 ComfyUI 抢同一张 8 GB 卡, OOM 就改 `device="cpu"`; ③ 抽帧时间点别超 `duration`(ffmpeg 退出码 0 但不生成文件, 末帧用 `时长 - 1/fps`); ④ **图与数字必须一起看** —— 纯音乐时 `pyin` 的 F0、以及"低谱平坦度 ⇒ 没雨声"的推断都会骗人, 频谱图能纠正。
