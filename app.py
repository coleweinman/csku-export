import os
import sys
import requests
import json
from datetime import datetime

headers = {
    'authorization': '',
}

subdomain = ""


def get_client_data(start, stop):
    params = {
        'company_type': 'CLIENT',
        'start-index': str(start),
        'max-results': str(stop - start),
        'order-by': 'client_name',
        'order-dir': 'asc',
        'search': 'true',
        'with_sales_report': 'false',
    }

    response = requests.get('https://{subdomain}.commonsku.com/v1/company/clients', params=params, headers=headers)

    client_data = response.json()["companies"]

    print(str(len(client_data)))
    for client in client_data:
        print("Getting file data for %s" % client["client_name"])
        if client['client_id'] != client['company_id']:
            print(client)

        params = {
            'parent_type': 'CLIENT',
            'parent_id': client['client_id'],
        }
        response = requests.get('https://{subdomain}.commonsku.com/v1/file', params=params, headers=headers)
        files = response.json()['files']
        need_folders = False
        for file in files:
            if file["folder_id"] != "":
                need_folders = True
                break
        if need_folders:
            folder_map = get_folder_info(client)
            for file in files:
                if file["folder_id"] != "":
                    if file["folder_id"] not in folder_map:
                        file["folder_id"] = ""
                    else:
                        file["folder_name"] = folder_map[file["folder_id"]]
        print("File count: %d" % len(files))
        client['files'] = files

    return client_data

def get_folder_info(client):
    params = {
        'parent_type': 'CLIENT',
        'parent_id': client['client_id'],
    }
    print("Getting folder info for %s" % client["client_name"])
    response = requests.get('https://{subdomain}.commonsku.com/v1/folder', params=params, headers=headers)
    folders = response.json()["folders"]
    folder_map = {}
    for folder in folders:
        folder_map[folder["folder_id"]] = folder["folder_name"].replace("/", "-")
    return folder_map

def download_files(output_path, client_data):
    for client in client_data:
        client["client_name"] = client["client_name"].replace("/", "-")
        folder_path = os.path.join(output_path, client["client_name"])
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
        for file in client["files"]:
            if file["folder_id"] != "":
                subfolder_path = os.path.join(output_path, client["client_name"], file["folder_name"])
                if not os.path.exists(subfolder_path):
                    os.mkdir(subfolder_path)
                path = os.path.join(output_path, client["client_name"], file["folder_name"], file["file_display_name"].replace("/", "-"))
            else:
                path = os.path.join(output_path, client["client_name"], file["file_display_name"].replace("/", "-"))
            if not os.path.exists(path):
                print("Downloading file for %s" % client["client_name"])
                response = requests.get(file["file_name_original"], allow_redirects=True)
                open(path, 'wb').write(response.content)
                create_date = datetime.strptime(file["date_created"], '%Y-%m-%d %H:%M:%S')
                os.utime(path, (int(create_date.timestamp()), int(create_date.timestamp())))
        last_used_date = datetime.strptime(client["latest_use"], '%Y-%m-%d %H:%M:%S')
        os.utime(folder_path, (int(last_used_date.timestamp()), int(last_used_date.timestamp())))

def organize_by_rep(start, stop):
    params = {
        'company_type': 'CLIENT',
        'start-index': str(start),
        'max-results': str(stop - start),
        'order-by': 'client_name',
        'order-dir': 'asc',
        'search': 'true',
        'with_sales_report': 'true',
    }

    response = requests.get('https://{subdomain}.commonsku.com/v1/company/clients', params=params, headers=headers)
    client_data = response.json()['companies']
    for client in client_data:
        name = client["client_name"].replace("/", "-")
        rep = client["client_rep_first_name"] + " " + client["client_rep_last_name"]
        if name == rep:
            continue
        print("Moving %s to %s" % (name, rep))
        folder_path = os.path.join("export", name)
        if not os.path.exists(folder_path):
            continue
        rep_folder_path = os.path.join("export", rep)
        new_folder_path = os.path.join("export", rep, name)
        if not os.path.exists(rep_folder_path):
            os.mkdir(rep_folder_path)
        if os.path.exists(folder_path):
            os.rename(folder_path, new_folder_path)

if __name__ == "__main__":
    print(f"Arguments count: {len(sys.argv)}")
    start = 0
    end = 0
    batch_size = 10
    output_path = "export"
    auth_file_path = "auth"
    for i, arg in enumerate(sys.argv):
        if arg == "-a":
            auth_file_path = sys.argv[i + 1]
        elif arg == "-s":
            start = int(sys.argv[i + 1])
        elif arg == "-e":
            end = int(sys.argv[i + 1])
        elif arg == "-b":
            batch_size = int(sys.argv[i + 1])
        elif arg == "-o":
            output_path = sys.argv[i + 1]
        elif arg == "-d":
            subdomain = sys.argv[i + 1]
        print(f"Argument {i:>6}: {arg}")

    with open(auth_file_path, 'r') as f:
        headers['authorization'] = f.readline()
    
    for i in range(start, end, batch_size):
        print("Trying %d - %d" % (i, i + batch_size))
        client_data = get_client_data(i, i + 10)
        download_files(output_path, client_data)




# organize_by_rep(2400, 3200)



