import pandas as pd
import requests
import json
import argparse

def login():
    """https://docs.github.com/en/developers/apps/authorizing-oauth-apps#device-flow"""
    request = json.loads(
        requests.post(
            "https://github.com/login/device/code",
            headers = {"Accept": "application/json"},
            data = {
                "client_id": "a405bf63b122619588c3",
                "scope": "repo"
                }
        ).content
    )
    input(f"Please navigate to {request['verification_uri']} and enter the code {request['user_code']}. Press enter when complete.")
    token = json.loads(
        requests.post(
            "https://github.com/login/oauth/access_token",
            headers = {"Accept": "application/json"},
            data = {
                "client_id": "a405bf63b122619588c3",
                "device_code": request["device_code"],
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                }
        ).content
    )
    return(token)

def get_stuff(api_call, token, params=None):
    stuff = json.loads(
        requests.get(
            api_call,
            headers = {
                "Accept": "application/vnd.github.inertia-preview+json",
                "Authorization": f"Bearer {token['access_token']}"
            },
            params=params
        ).content
    )
    return(stuff)

def get_cards(api_call, token):
    """The GitHub API only allows requesting up to 100 cards at a time. This grabs all cards by navigating the pages."""
    cards = []
    n = 1
    while True:
        response = get_stuff(api_call, token, params={"per_page": 100, "page": n})
        cards.extend(response)
        if len(response) == 100:
            n = n + 1
            continue
        else:
            return(cards)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="A utility for grabbing cards/issues and their data out of a github project into a .csv file.")
    parser.add_argument("-t", "--personal-token", help="Provide a personal token for use with Github API. See https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token.")
    parser.add_argument("-p", "--project-id", help="Provide a project ID to pull details for.")
    parser.add_argument("-o", "--outfile", help="Specify a path to write the output csv.")
    args = parser.parse_args()

    if args.personal_token:
        token = {"access_token": args.personal_token}
    else:
        token = login()

    if args.project_id:
        project_id = args.project_id
    else:
        project_boards = get_stuff("https://api.github.com/orgs/GSS-Cogs/projects", token)
        boards_df = pd.DataFrame.from_dict([{"name" : x["name"], "id": x["id"]} for x in project_boards]).sort_values("name")
        print(f"Please select a project id: \n {boards_df}")
        project_id = input("project_id: ")

    data = []

    project_board = get_stuff(f"https://api.github.com/projects/{project_id}", token)

    project_columns = get_stuff(project_board["columns_url"], token)

    for column in project_columns:
        cards = get_cards(column["cards_url"], token)
        for card in cards:
            item = {
                "project_name": project_board["name"],
                "project_url": project_board["html_url"],
                "column_name": column["name"],
                "archived": card["archived"],
                "created_at": card["created_at"],
                "updated_at": card["updated_at"]
            }
            if card.get("content_url"):
                card_content = get_stuff(card["content_url"], token)
                item["issue_url"] = card_content["html_url"]
                item["repository"] = card_content["repository_url"].split("/")[-1]
                item["number"] = int(card_content["number"])
                item["state"] = card_content["state"]
                item["title"] = card_content["title"]
                item["notes"] = card_content["body"]
                item["labels"] = [label["name"] for label in card_content["labels"]]
                item["assignee"] = card_content["assignee"]["login"] if card_content.get("assignee") else None
                item["author"] = card_content["user"]["login"]
                item["locked"] = card_content["locked"]
            else:
                item["notes"] = card["note"]
                item["author"] = card["creator"]["login"]

            data.append(item)

    df = pd.DataFrame.from_dict(data)

    if args.outfile:
        out_filepath = args.outfile
    else:
        out_filepath = "output.csv"

    df.to_csv(
        out_filepath, 
        index=False,
        columns=['project_name', 'project_url', 'column_name', 'archived', 'created_at', 'updated_at', 'notes', 
                 'author', 'issue_url', 'repository', 'number', 'state', 'title', 'labels', 'assignee', 'locked']
    )