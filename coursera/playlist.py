import glob
import os


def create_m3u_playlist(section_dir):
    """
    Create M3U playlist with contents of `section_dir`/*.mp4. The playlist
    will be created in that directory.

    @param section_dir: Path where to scan for *.mp4 files.
    @type section_dir: str
    """
    path_to_return = os.getcwd()

    for (_path, subdirs, files) in os.walk(section_dir):
        os.chdir(_path)
        globbed_videos = sorted(glob.glob("*.mp4"))
        m3u_name = os.path.split(_path)[1] + ".m3u"

        if len(globbed_videos):
            with open(m3u_name, "w") as m3u:
                for video in globbed_videos:
                    m3u.write(video + "\n")
            os.chdir(path_to_return)
    os.chdir(path_to_return)
