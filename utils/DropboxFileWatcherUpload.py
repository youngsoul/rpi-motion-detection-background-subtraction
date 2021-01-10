from utils.BackgroundFileProcessor import BackgroundFileProcessor
from pathlib import Path
import dropbox
from dropbox.exceptions import ApiError

class DropboxFileWatcherUpload(BackgroundFileProcessor):
    def _upload_file(self, file_from, file_to):
        dbx = dropbox.Dropbox(self.dropbox_access_token)

        with open(file_from, 'rb') as f:
            dbx.files_upload(f.read(), file_to)

    def __init__(self, dropbox_access_token: str,  root_dir: str, include_parent_dir_in_to_file=True, pattern:str="*", delete_after_process: bool=False, batch_size: int=10, polling_time: int=5 ):
        BackgroundFileProcessor.__init__(self, root_dir, pattern, delete_after_process, batch_size, polling_time)

        self.include_parent_dir_in_to_file = include_parent_dir_in_to_file
        self.dropbox_access_token = dropbox_access_token

    def process_file(self, absolute_file_path):
        print(absolute_file_path)
        p = Path(absolute_file_path)
        if self.include_parent_dir_in_to_file:
            to_path = f"/{p.parent.name}/{p.name}"
        else:
            to_path = p.name

        try:
            self._upload_file(absolute_file_path, to_path)
        except ApiError as err:
            # Check user has enough Dropbox space quota
            if (err.error.is_path() and
                    err.error.get_path().error.is_insufficient_space()):
                print("ERROR: Cannot upload; insufficient space.")
            elif err.user_message_text:
                print(err.user_message_text)

            else:
                print(err)




if __name__ == '__main__':
    from dotenv import load_dotenv
    import os

    load_dotenv()
    env_path = Path('.') / '.env'
    load_dotenv(dotenv_path=env_path)

    access_token = os.getenv('dropbox_access_token')

    db = DropboxFileWatcherUpload(dropbox_access_token=access_token, root_dir="../motion", pattern="*.jpg", delete_after_process=True)

    db.start()

    db.drain()

