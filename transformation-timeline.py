from functools import lru_cache

from github import Github, UnknownObjectException, GithubException
import json

with open('.token') as tf:
    token = tf.readline()

g = Github(token)

family_repos = [repo for repo in g.get_user().get_repos() if repo.name.startswith('family-')]


@lru_cache
def get_project(id):
    return g.get_project(id)


for family in family_repos:
    try:
        ds_info = json.loads(family.get_contents('datasets/info.json').decoded_content)
    except GithubException:
        print(f'{family.name} has no datasets/info.json file')
        continue
    for pipeline in ds_info['pipelines']:
        try:
            pipeline_info = json.loads(family.get_contents(f'datasets/{pipeline}/info.json').decoded_content)
            pipeline_issue_no = pipeline_info['transform']['main_issue']
            pipeline_issue = family.get_issue(pipeline_issue_no)
        except GithubException:
            print(f'{pipeline} has no info.json file')
            continue
        for event in pipeline_issue.get_timeline():
            print(f'{pipeline}: {event.event} {event.created_at}')
            if event.event in ['added_to_project', 'moved_columns_in_project']:
                project_id = event.raw_data['project_card']['project_id']
                column = event.raw_data['project_card']['column_name']
                print(f'{get_project(project_id).name} - {column}')
