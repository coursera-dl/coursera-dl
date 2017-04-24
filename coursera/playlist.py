import os
import glob


def create_m3u_playlist(section_dir):
    """
    Create M3U playlist with contents of `section_dir`/*.mp4. The playlist
    will be created in that directory.

    @param section_dir: Path where to scan for *.mp4 files.
    @type section_dir: str
    """
    path_to_return = os.getcwd()

    for (_path, subdirs, files) in os.walk(section_dir, topdown=False):
        os.chdir(_path)
        globbed_videos = sorted(glob.glob("*.mp4"))
        m3u_name = os.path.split(_path)[1] + ".m3u"

        if not len(globbed_videos):
            for subdir in subdirs:
                for fname in os.listdir(subdir):
                    if fname.endswith(".m3u"):
                        with open(os.path.join(subdir, fname)) as f:
                            for line in f.readlines():
                                globbed_videos.append(os.path.join(subdir, line.strip()))

        if len(globbed_videos):
            with open(m3u_name, "w") as m3u:
                for video in globbed_videos:
                    m3u.write(video + "\n")

    os.chdir(path_to_return)


if __name__ == "__main__":
    create_m3u_playlist(os.getcwd())
