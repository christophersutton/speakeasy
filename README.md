# speakeasy

Quick voice note transcription using Whisper locally on Apple Silicon. Use hotkeys to record audio and output the transcription to a file or your clipboard.

Speech recognition with Whisper[^1] in Apple's MLX[^2].

### Setup

Install the dependencies.

```
pip install -r requirements.txt
```

Install [`ffmpeg`](https://ffmpeg.org/):

```
# on macOS using Homebrew (https://brew.sh/)
brew install ffmpeg
```
If desired can update the hotkeys. Currently set to cmd+ctrl then j for saving and l for clipboard. The Hotkeys class of pynput doesn't have key release support so not using it - this way you can just hold down the cmd after triggering the recording rather than holding down all keys with both hands. 

### Run

Run the script in the background using nohup, tmux etc

[^1]: Refer to the [arXiv paper](https://arxiv.org/abs/2212.04356), [blog post](https://openai.com/research/whisper), and [code](https://github.com/openai/whisper) for more details.
[^2]: Apple released a machine learning framework for Apple Silicon without much noise or fanfare. [Framework here](https://github.com/ml-explore/mlx) and [Whisper implementation here](https://github.com/ml-explore/mlx-examples/tree/main/whisper)
