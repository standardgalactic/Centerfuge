
# Appendix H — AV Sync
ffmpeg -framerate 24 -pattern_type glob -i "frames_*.png" -crf 18 -vcodec libx264 visuals.mp4
ffmpeg -i visuals.mp4 -i scene_audio.wav -c:v copy -c:a aac -b:a 192k -shortest composite.mp4
