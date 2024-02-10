#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Zachary LeBlanc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, annotations, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "supported_by": "community",
}

DOCUMENTATION = r"""
---
module: favorite_movies_info
author: "Zach LeBlanc (@zjleblanc)"
short_description: Update Favorite Movies for a TMDB account
description:
  - This module gets movies favorited by a specified TMDB account
options:
  api_url:
    description:
      - Base url for the TMDB API
    type: str
    required: true
    version_added: "1.0.0"
  api_key:
    description:
      - Api Key for the TMDB API
    type: str
    required: true
    version_added: "1.0.0"
  username:
    description:
      - Username for the TMDB API
    type: str
    required: true
    version_added: "1.0.0"
  password:
    description:
      - Password for the TMDB API
    type: str
    required: true
    version_added: "1.0.0"
  account_id:
    description:
      - Account ID to retrieve favorite movies from
    type: str
    required: true
    version_added: "1.0.0"
  movie_id:
    description:
      - "Movie ID to update favorite status (found in URL of movie page)"
    type: str
    required: true
    version_added: "1.0.0"
  state:
    description:
      - Whether or not the movie should be favorited for the account
      - Added to favorites if O(state=present), removed if O(state=absent)
    type: str
    choices:
      - present
      - absent
    required: true
    version_added: "1.0.0"
attributes:
  platform:
    platforms: all
"""

EXAMPLES = r"""
- name: Add a favorite movie
  zjleblanc.tmdb.favorite_movies:
    account_id: 12345
    movie_id: 09876

- name: Remove a favorite movie
  zjleblanc.tmdb.favorite_movies:
    account_id: 12345
    movie_id: 09876
    state: absent
"""

RETURN = r"""
favorites:
  description: List of favorite movies
  returned: success
  type: list
  elements: dict
  sample:
    - adult: false
      backdrop_path: "/fm6KqXpk3M2HVveHwCrBSSBaO0V.jpg"
      genre_ids:
        - 18
        - 36
      id: 872585
      original_language: en
      original_title: Oppenheimer
      overview: The story of J. Robert Oppenheimer's role in the development of the atomic bomb during World War II.
      popularity: 437.917
      poster_path: "/ptpr0kGAckfQkJeJIt8st5dglvd.jpg"
      release_date: '2023-07-19'
      title: Oppenheimer
      video: false
      vote_average: 8.1
      vote_count: 6610
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ..module_utils import client, errors
import json

def is_favorite(movie_id: str, favorites: list) -> bool:
  for fav in favorites:
    if str(fav['id']) == movie_id:
      return True
  return False

def main():
  arg_spec = dict(
    api_url=dict(
      type="str",
      required=True,
      fallback=(env_fallback, ["TMDB_API"]),
    ),
    api_key=dict(
      type="str",
      required=True,
      fallback=(env_fallback, ["TMDB_API_KEY"]),
      no_log=True,
    ),
    username=dict(
      type="str",
      required=True,
      fallback=(env_fallback, ["TMDB_USERNAME"]),
    ),
    password=dict(
      type="str",
      required=True,
      fallback=(env_fallback, ["TMDB_PASSWORD"]),
      no_log=True,
    ),
    account_id=dict(
      type="str",
      required=True,
      fallback=(env_fallback, ["TMDB_ACCOUNT_ID"]),
    ),
    movie_id=dict(
      type="str",
      required=True,
    ),
    state=dict(
      type="str",
      default='present',
      choices=['present', 'absent'],
    ),
  )

  module = AnsibleModule(
    supports_check_mode=True,
    argument_spec=arg_spec,
  )

  try:
    tmdb_client = client.TMDBClient(**module.params)
    tmdb_client.login()
    response = tmdb_client.get(f"/account/{module.params['account_id']}/favorite/movies")
    favorites = json.loads(response.read()).get('results')

    state = module.params['state']
    movie_id = module.params['movie_id']
    favorited = is_favorite(movie_id, favorites)
    payload = dict(
      media_type='movie',
      movie_id=movie_id,
      favorite=(state == 'present')
    )

    if state == 'present' and favorited:
      module.exit_json(changed=False, favorites=favorites)
    elif state == 'present' and not favorited:
      tmdb_client.post(f"/account/{module.params['account_id']}/favorite", payload)
      response = tmdb_client.get(f"/account/{module.params['account_id']}/favorite/movies")
      changed_favorites = json.loads(response.read()).get('results')
      module.exit_json(changed=True, favorites=changed_favorites)
    elif state == 'absent' and not favorited:
      module.exit_json(changed=False, favorites=favorites)
    elif state == 'absent' and favorited:
      tmdb_client.post(f"/account/{module.params['account_id']}/favorite", payload)
      changed_favorites = filter(lambda movie: str(movie['id']) != movie_id, favorites)
      module.exit_json(changed=True, favorites=list(changed_favorites))
    else:
      raise errors.TMDBException(f"Unexpected state: {state}")
  except errors.TMDBException as e:
    module.fail_json(msg=str(e))

if __name__ == "__main__":
  main()