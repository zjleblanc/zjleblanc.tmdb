<#
.SYNOPSIS
	Manages TMDB Account Favorites using the TMDB API
.DESCRIPTION
	This PowerShell script queries Favorite movies for a given TMDB account. It also adds/removes a Favorite to demonstrate interaction with the TMDB API.
.PARAMETER AccountId
	Specifies the TMDB Account Id.
.PARAMETER MovieId
	Specifies the TMDB Movie Id to add/remove from Favorites (for demonstration purposes).
.EXAMPLE
	PS> ./tmdb.ps1 -AccountId 12345 -MovieId 09876
.LINK
	https://github.com/zjleblanc/zjleblanc.tmdb/blob/master/docs/tmdb.ps1
.NOTES
	Author: Zachary LeBlanc
#>

<#
ENVIRONMENT VARIABLES:
  - TMDB_API
  - TMDB_API_KEY
  - TMDB_USERNAME
  - TMDB_PASSWORD
#>

param(
  [Parameter(mandatory=$true)]
	[string]$AccountId,
  [Parameter(mandatory=$true)]
	[string]$MovieId
)

function Test-Favorite {
  param ($TestMovieId, $TestFavorites)

  foreach ($movie in $TestFavorites) {
    if($movie.id -eq $TestMovieId) {
      return $true;
    }
  }

  return $false;
}

# Create request token
$url = "$env:TMDB_API/authentication/token/new?api_key=$env:TMDB_API_KEY"
$Token = (Invoke-WebRequest -Uri $url -Method GET -UseBasicParsing | ConvertFrom-Json).request_token

# Validate token with login
$url = "$env:TMDB_API/authentication/token/validate_with_login?api_key=$env:TMDB_API_KEY"
$body = @{ 
  'username' = $env:TMDB_USERNAME
  'password' = $env:TMDB_PASSWORD
  'request_token' = $Token 
}
Invoke-WebRequest -Uri $url -Method POST -ContentType "application/json" -Body ($body|ConvertTo-Json) | Out-Null

# Create session
$url = "$env:TMDB_API/authentication/session/new?api_key=$env:TMDB_API_KEY"
$body = @{
  'request_token' = $Token 
}
$Session = (Invoke-WebRequest -Uri $url -Method POST -ContentType "application/json" -Body ($body|ConvertTo-Json) -UseBasicParsing | ConvertFrom-Json).session_id

# Build auth query params
$AuthQuery="api_key=$env:TMDB_API_KEY&session_id=$Session"

# Get favorite movies
$url = "$env:TMDB_API/account/$AccountId/favorite/movies?$AuthQuery"
$favorites = (Invoke-WebRequest -Uri $url -Method GET -UseBasicParsing | ConvertFrom-Json).results

# Add Dune to favorite movies
if(Test-Favorite -TestMovieId $MovieId -TestFavorites $favorites) {
  Write-Host -ForegroundColor Green "[ok] Add Dune to favorite movies"
}
else {
  $url = "$env:TMDB_API/account/$AccountId/favorite?$AuthQuery"
  $body = @{ 
    'media_type' = 'movie'
    'media_id' = $MovieId
    'favorite' = $true
  }
  $Response = (Invoke-WebRequest -Uri $url -Method POST -ContentType "application/json" -Body ($body|ConvertTo-Json) -UseBasicParsing | ConvertFrom-Json).status_message
  Write-Host -ForegroundColor Yellow "[changed] Add Dune to favorite movies"
}

# Get favorite movies
$url = "$env:TMDB_API/account/$AccountId/favorite/movies?$AuthQuery"
$favorites = (Invoke-WebRequest -Uri $url -Method GET -UseBasicParsing | ConvertFrom-Json).results

# Remove Dune from favorite movies
if(Test-Favorite -TestMovieId $MovieId -TestFavorites $favorites) {
  $url = "$env:TMDB_API/account/$AccountId/favorite?$AuthQuery"
  $body = @{ 
    'media_type' = 'movie'
    'media_id' = $MovieId
    'favorite' = $false
  }
  $Response = (Invoke-WebRequest -Uri $url -Method POST -ContentType "application/json" -Body ($body|ConvertTo-Json) -UseBasicParsing | ConvertFrom-Json).status_message
  Write-Host -ForegroundColor Yellow "[changed] Remove Dune from favorite movies"
}
else {
  Write-Host -ForegroundColor Green "[ok] Remove Dune from favorite movies"
}

# Get favorite movies after removing Dune
$url = "$env:TMDB_API/account/$AccountId/favorite/movies?$AuthQuery"
$favorites = (Invoke-WebRequest -Uri $url -Method GET -UseBasicParsing | ConvertFrom-Json).results
Write-Host ($favorites | Select title)