import logging
from logging import config
from os import path

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

config.fileConfig('resources/logging.cfg')

class DriveException(Exception):
    pass


class Drive:
    def __init__(self):
        self.drive = self.__auth()
        self.drive_id = 'ID of the shared drive the file resides in. Only populated for items in shared drives.'

    @staticmethod
    def __auth():
        g_auth = GoogleAuth(settings_file='settings.yaml')
        g_auth.LocalWebserverAuth()
        g_drive = GoogleDrive(g_auth)
        logging.info('Successful authentication on Drive')
        return g_drive

    def get_files(self, folder_id):
        file_list = self.drive.ListFile({'q': f'"{folder_id}" in parents and trashed=false'}).GetList()

        if file_list:
            for file in file_list:
                logging.debug(f'tittle: {file["title"]}, id {file["id"]}')
        else:
            logging.info('Empty Folder')
            file_list = []

        return file_list

    def search_file(self, folder_id, file_name):
        file_list = self.get_files(folder_id)
        file = None

        for file1 in file_list:
            if file_name.lower() == file1['title'].lower():
                logging.info(f'tittle: {file1["title"]}, id {file1["id"]}')
                file = file1
                break

        return file

    def create_dir(self, folder_id, folder_name):
        sub_folder = folder_name.split('/', 1)

        file = self.search_file(folder_id, sub_folder[0])
        if file is None:
            new_folder = {
                'title': sub_folder[0],
                'parents': [{'id': folder_id}],
                "mimeType": "application/vnd.google-apps.folder"
            }
            file = self.drive.CreateFile(new_folder)
            file.Upload()

            logging.info(f'{sub_folder[0]} folder created successfully')
            logging.debug(f'tittle: {file["title"]}, id {file["id"]}')

        if len(sub_folder) > 1:
            file = self.create_dir(file['id'], sub_folder[1])

        return file

    def upload_file(self, folder_id, file_path):
        file = self.search_file(folder_id, path.basename(file_path))

        # Create new file is not exists else update it
        if file is None:
            metadata = {
                # 'driveId': self.drive_id
                'parents': [{'id': folder_id}],
                'title': path.basename(file_path)
            }
            logging.debug(f'File parameters: {metadata}')
            file = self.drive.CreateFile(metadata)

        file.SetContentFile(file_path)
        file.Upload()
        logging.info(f'{file["title"]} uploaded successfully')
        logging.debug(f'tittle: {file["title"]}, id {file["id"]}')

    def download_file(self, folder_id, file_name, local_dir):
        file1 = self.search_file(folder_id, file_name)
        file2 = self.drive.CreateFile({'id': file1['id']})
        file2.GetContentFile(path.join(local_dir, file_name))
        logging.info(f'File downloaded successfully to {path.join(local_dir, file_name)}')

    def trash_file(self, folder_id, file_name):
        file = self.search_file(folder_id, file_name)
        file.Trash()
        logging.info(f'{file_name} deleted successfully')

    def diff_local_remote_dir(self, folder_id, local_files):
        file_list1 = self.get_files(folder_id)
        file_list2 = [file['title'] for file in file_list1]
        remote_files = set(file_list2)

        diff_files = remote_files.difference(local_files)
        logging.info(f'Diff files: {diff_files}')
        return diff_files


if __name__ == '__main__':
    g = Drive()
