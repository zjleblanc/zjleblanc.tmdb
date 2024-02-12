#!/bin/bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

: '
usage:
  - tmdb.sh 12345
requirements:
  system:
    - curl
    - jq
  env:
    - TMDB_API
    - TMDB_API_KEY
    - TMDB_USERNAME
    - TMDB_PASSWORD
'
ACCOUNT_ID=$1
MOVIE_ID=$2

is_favorite () {
  favorites=$1
  movie_id=$2

  if [[ $favorites == *"\"id\": $movie_id"* ]]
  then
    return 1
  else
    return 0
  fi
} 

# Create request token
TOKEN=$(
  curl -s --request GET \
    --url $TMDB_API/authentication/token/new?api_key=$TMDB_API_KEY \
    | jq '.request_token'
)

# Validate token with login
curl -s --request POST \
    --url $TMDB_API/authentication/token/validate_with_login?api_key=$TMDB_API_KEY \
    --header 'accept: application/json' \
    --header 'content-type: application/json' \
    -d '{"username": "'$TMDB_USERNAME'", "password": "'$TMDB_PASSWORD'", "request_token": '$TOKEN'}' \
    > /dev/null

# Create session
SESSION=$(
  curl -s --request POST \
    --url $TMDB_API/authentication/session/new?api_key=$TMDB_API_KEY \
    --header 'accept: application/json' \
    --header 'content-type: application/json' \
    -d '{"request_token": '$TOKEN'}' \
    | jq -r '.session_id'
)

# Build auth query params
AUTH_QUERY="api_key=$TMDB_API_KEY&session_id=$SESSION"

# Get favorite movies
FAVORITES=$(
  curl -s --request GET \
    --url $TMDB_API/account/$ACCOUNT_ID/favorite/movies?$AUTH_QUERY \
    | jq '.results'
)

# Add Dune to favorite movies
is_favorite "$FAVORITES" $MOVIE_ID
if [ $? -eq 0 ]
then
  curl -s --request POST \
      --url $TMDB_API/account/$ACCOUNT_ID/favorite?$AUTH_QUERY \
      --header 'accept: application/json' \
      --header 'content-type: application/json' \
      -d '{"media_type": "movie", "media_id": '$MOVIE_ID', "favorite": true}' \
      | jq '.status_message' > /dev/null
  echo -e "${YELLOW}[changed] Add dune to favorites${NC}"
else
  echo -e "${GREEN}[ok] Add dune to favorites${NC}"
fi

# Get favorite movies after adding Dune
FAVORITES=$(
  curl -s --request GET \
    --url $TMDB_API/account/$ACCOUNT_ID/favorite/movies?$AUTH_QUERY \
    | jq '.results'
)

# Remove Dune from favorite movies
is_favorite "$FAVORITES" $MOVIE_ID
if [ $? -ne 0 ]
then
  curl -s --request POST \
      --url $TMDB_API/account/$ACCOUNT_ID/favorite?$AUTH_QUERY \
      --header 'accept: application/json' \
      --header 'content-type: application/json' \
      -d '{"media_type": "movie", "media_id": '$MOVIE_ID', "favorite": false}' \
      | jq '.status_message' > /dev/null
  echo -e "${YELLOW}[changed] Remove Dune from favorite movies${NC}"
else
  echo -e "${GREEN}[ok] Remove Dune from favorite movies${NC}"
fi

# Get favorite movies after removing Dune
echo -e "${GREEN}[ok] Debug end state | favorite titles${NC}"
curl -s --request GET \
  --url $TMDB_API/account/$ACCOUNT_ID/favorite/movies?$AUTH_QUERY \
  | jq '.results[].title'
