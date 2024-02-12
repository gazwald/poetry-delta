import shutil
import os
from datetime import datetime
import toml


def find_pyproject_path():
    current_dir = os.getcwd()
    while current_dir != "/":
        pyproject_path = os.path.join(current_dir, "pyproject.toml")
        if os.path.isfile(pyproject_path):
            return pyproject_path
        current_dir = os.path.dirname(current_dir)
    print("pyproject.toml not found in the current directory or any parent directory.")
    return None


def get_poetry_project_name(pyproject_path):
    if pyproject_path:
        with open(pyproject_path, 'r') as f:
            pyproject_data = toml.load(f)
        return pyproject_data.get('tool', {}).get('poetry', {}).get('name')
    return None


def get_save_dir(project_name, backup_dir):
    project_save_dir = os.path.join(backup_dir, project_name)
    datecode = datetime.now().strftime("%Y%m%d_%H%M")
    save_dir = os.path.join(project_save_dir, datecode)
    os.makedirs(backup_dir, exist_ok=True)
    os.makedirs(project_save_dir, exist_ok=True)
    os.makedirs(save_dir, exist_ok=True)
    return project_save_dir, save_dir


def get_autosave_dir(project_name, backup_dir):
    project_save_dir = os.path.join(backup_dir, project_name)
    tmp_dir = os.path.join(project_save_dir, "tmp")
    os.makedirs(backup_dir, exist_ok=True)
    os.makedirs(project_save_dir, exist_ok=True)
    os.makedirs(tmp_dir, exist_ok=True)
    return project_save_dir, tmp_dir


def backup_project(pyproject_path):
    project_name = get_poetry_project_name(pyproject_path)
    if project_name:
        _, save_dir = get_save_dir(project_name, backup_dir)
        try:
            shutil.copy2(os.path.join(pyproject_path, "pyproject.toml"), save_dir)
            shutil.copy2(os.path.join(pyproject_path, "poetry.lock"), save_dir)
            shutil.copy2(os.path.join(pyproject_path, "requirements.txt"), save_dir)
            print("Backup created successfully.")
        except FileNotFoundError:
            print("Failed to create backup. Some files not found.")


def autosave_project(pyproject_path):
    project_name = get_poetry_project_name(pyproject_path)
    if project_name:
        _, tmp_dir = get_autosave_dir(project_name, backup_dir)
        try:
            shutil.copy2(os.path.join(pyproject_path, "pyproject.toml"), os.path.join(tmp_dir, "pyproject.toml.bak"))
            shutil.copy2(os.path.join(pyproject_path, "poetry.lock"), os.path.join(tmp_dir, "poetry.lock.bak"))
            print("Autosave created successfully.")
        except FileNotFoundError:
            print("Failed to create autosave. Some files not found.")


def get_autosave():
    project_name = get_poetry_project_name(find_pyproject_path())
    if project_name:
        _, tmp_dir = get_autosave_dir(project_name, backup_dir)
        autosave_path = os.path.join(tmp_dir, "poetry.lock.bak")
        if os.path.exists(autosave_path):
            return autosave_path
        else:
            print("Autosave not found.")
    else:
        print("Poetry project name not found.")
    return None


def get_last_backup():
    project_name = get_poetry_project_name(find_pyproject_path())
    if project_name:
        _, save_dir = get_save_dir(project_name, backup_dir)
        try:
            with os.scandir(save_dir) as entries:
                backups = [entry.name for entry in entries if entry.is_dir()]
                if backups:
                    last_backup = max(backups)
                    print("Found Backup from:", os.path.basename(last_backup))
                    return last_backup
                else:
                    print("No backups found.")
        except FileNotFoundError:
            print("Failed to retrieve backups. Directory not found.")
    else:
        print("Poetry project name not found.")
    return None