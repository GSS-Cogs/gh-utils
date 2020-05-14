from functools import lru_cache

from github import Github, UnknownObjectException, GithubException
import json
from json.decoder import JSONDecodeError

with open('.token') as tf:
    token = tf.readline()

g = Github(token)

family_repos = [repo for repo in g.get_user().get_repos() if repo.name.startswith('family-')]


@lru_cache
def get_project(id):
    return g.get_project(id)


events = []

for family in family_repos:
    try:
        ds_info = json.loads(family.get_contents('datasets/info.json').decoded_content)
    except GithubException:
        print(f'{family.name} has no datasets/info.json file')
        continue
    except JSONDecodeError:
        print(f'{family.name} problem parsing JSON in datasets/info.json file')
        continue
    for pipeline in ds_info['pipelines']:
        try:
            pipeline_info = json.loads(family.get_contents(f'datasets/{pipeline}/info.json').decoded_content)
            if 'transform' in pipeline_info and 'main_issue' in pipeline_info['transform']:
                pipeline_issue_no = pipeline_info['transform']['main_issue']
                pipeline_issue = family.get_issue(pipeline_issue_no)
            else:
                continue
        except GithubException:
            print(f'{family.name} has no datasets/{pipeline}/info.json file')
            continue
        except JSONDecodeError:
            print(f'{family.name} problem parsing datasets/{pipeline}/info.json file')
            continue
        for event in pipeline_issue.get_timeline():
            print(f'{pipeline}: {event.event} {event.created_at}')
            events.append((event.created_at, event.raw_data))
#            if event.event in ['added_to_project', 'moved_columns_in_project']:
#                project_id = event.raw_data['project_card']['project_id']
#                column = event.raw_data['project_card']['column_name']
#                print(f'{get_project(project_id).name} - {column}')

timeline = [e[1] for e in sorted(events, key=lambda x: x[0])]

with open('timeline.json', 'w') as timeline_file:
    json.dump(timeline, timeline_file)
