import traceback 
import jwt
import os
from urllib.parse import urlparse

from backend.utils.setupenv import get_required_env_value, normalize_url_for_runtime


MEDIATHEKEN_SENTINEL = "Mediatheken"


def is_mediatheken_provider(provider: str) -> bool:
  normalized_provider = str(provider or "").strip().casefold()
  return normalized_provider in {
      "mediatheken",
      "mediathek",
      "ard mediathek",
      "zdf mediathek",
      "arte",
      "arte mediathek",
      "3sat",
      "3sat mediathek",
  }


def split_streaming_and_mediatheken(providers: list[str]) -> tuple[list[str], bool]:
  streaming_providers: list[str] = []
  seen_streaming: set[str] = set()
  include_mediatheken = False

  for provider in providers:
    normalized_provider = str(provider or "").strip()
    if not normalized_provider:
      continue

    if is_mediatheken_provider(normalized_provider):
      include_mediatheken = True
      continue

    dedupe_key = normalized_provider.casefold()
    if dedupe_key in seen_streaming:
      continue

    seen_streaming.add(dedupe_key)
    streaming_providers.append(normalized_provider)

  return streaming_providers, include_mediatheken


def choose_streaming_providers(userstreamingproviders: list[str], paymenttypes: list[str]) -> list[str]:
  from backend.utils.tmdb.common import FreeProvider, Provider

  """
  Filter streaming providers based on payment types.
  - If paymenttypes contains only 'free': filter against FreeProvider and return matched FreeProvider values
  - If paymenttypes contains 'rent' (or mixed types): filter against BOTH Provider and FreeProvider enums
  
  Uses conservative fuzzy matching to handle expected variants like:
  - "Amazon" -> "Amazon Prime Video"
  - "Magenta TV" -> "Magenta TV+"
  while avoiding false positives like "Disney Plus" -> "Paramount Plus".
  """
  def normalize(value: str) -> str:
    return value.lower().replace(' ', '').replace('+', '').replace('-', '')

  def significant_tokens(value: str) -> set[str]:
    stop_tokens = {"plus", "tv", "video"}
    tokens = value.lower().replace('+', ' ').replace('-', ' ').split()
    return {token for token in tokens if token and token not in stop_tokens}

  def is_match(user_provider: str, reference_provider: str) -> bool:
    user_lower = user_provider.lower()
    ref_lower = reference_provider.lower()

    if user_lower == ref_lower:
      return True

    user_norm = normalize(user_provider)
    ref_norm = normalize(reference_provider)

    if user_norm == ref_norm:
      return True

    user_sig = significant_tokens(user_provider)
    ref_sig = significant_tokens(reference_provider)

    shared_sig = user_sig & ref_sig
    if not shared_sig:
      return False

    return (
      user_norm in ref_norm
      or ref_norm in user_norm
      or user_lower in ref_lower
      or ref_lower in user_lower
      or user_sig.issubset(ref_sig)
      or ref_sig.issubset(user_sig)
    )

  # Determine which enum(s) to use based on payment types
  if paymenttypes == ["free"] or paymenttypes == ["flatrate"]:
    # Only free content - use FreeProvider
    reference_providers = [fp.value for fp in FreeProvider]
  else:
    # Rent or mixed payment types - use BOTH enums while preserving deterministic order
    reference_providers = [p.value for p in Provider]
    for free_provider in [fp.value for fp in FreeProvider]:
      if free_provider not in reference_providers:
        reference_providers.append(free_provider)
  
  filtered_providers = []
  seen = set()
  streaming_providers, _include_mediatheken = split_streaming_and_mediatheken(userstreamingproviders)
  for user_provider in streaming_providers:
    for ref_provider in reference_providers:
      if is_match(user_provider, ref_provider) and ref_provider not in seen:
        seen.add(ref_provider)
        filtered_providers.append(ref_provider)
  
  return filtered_providers
  
  
  
def get_movie_data(input: dict):
  try:
    from backend.utils.tmdb.tmdb_api_client import get_basic_data_from_tmdb_for_titles

    titles = input["titles"]
    print(f"_get_movie_data titles input: ", titles)
    inputlist = titles.split(",")
    inputlist = [x.strip(' ') for x in inputlist]      
    result = get_basic_data_from_tmdb_for_titles(inputlist)
    print(f"get_movie_data result: ", result)
    return result
  except:    
     traceback.print_exc() 
     return None

def get_filtered_titles_tmdb(titles: list, userstreamingproviders: list[str]) -> dict:
  """Get filtered titles. Accepts list of strings or list of dicts with media_type."""
  try:
    from backend.utils.tmdb.tmdb_api_client import get_movies_for_providers

    inputlist = titles
    providers = userstreamingproviders
    print(f"_get_movie_data titles input: ", titles, "filtered by providers: ", providers)
    result = get_movies_for_providers(inputlist, providers)    
    print(f"get_tmdb_filtered_movies result: ",result)
    return result  
  except:
      traceback.print_exc() 
      return None 
    
def get_filtered_recros_titles_tmdb(titles: list[str], userstreamingproviders: list[str]) -> dict:
  try:
    inputlist = titles
    providers = userstreamingproviders
    print(f"_get_movie_data titles input: ", titles, "filtered by providers: ", providers)
    #inputlist = titles.split(",")
    #inputlist = [x.strip(' ') for x in inputlist]
    result = get_filtered_recros_titles_tmdb(inputlist, providers)
    print(f"get_recro_movies result: ",result)
    return result  
  except:
      traceback.print_exc() 
      return None     

def get_streaming_providers_tmdb(titles: list[str]):
  try:
    from backend.utils.tmdb.tmdb_api_client import get_basic_data_from_tmdb_for_titles

    print(f"get_streaming_providers","titles=",titles)
    result = get_basic_data_from_tmdb_for_titles(titles)
    print(f"get_streaming_providers","result:", result)
    return result
  except:
     traceback.print_exc() 
     return None

def get_detail_moviedata(title: str):
  try:
    from backend.utils.tmdb.tmdb_api_client import get_detail_data_from_tmdb_for_title

    print(f"get_movie_data_from_tmdb","title=",title)
    fulldata = get_detail_data_from_tmdb_for_title(title)
    print(f"get_detail_moviedata","result:", fulldata)
    return fulldata
  except:
     traceback.print_exc() 
     return None


def verify_and_decode_supabase_jwt(token: str) -> dict:
  """Validate and decode a Supabase JWT token using HS256 secret."""
  audience = os.getenv("SUPABASE_JWT_AUDIENCE", "authenticated")
  unverified_header = jwt.get_unverified_header(token)
  algorithm = str(unverified_header.get("alg", "")).upper()

  if algorithm.startswith("HS"):
    secret = get_required_env_value("SUPABASE_JWT_SECRET")
    return jwt.decode(
        token,
        secret,
        algorithms=[algorithm],
        audience=audience,
        options={"require": ["sub", "exp"]},
    )

  unverified_claims = jwt.decode(token, options={"verify_signature": False})
  issuer = str(unverified_claims.get("iss", ""))
  if not issuer:
    raise jwt.InvalidTokenError("Missing issuer claim")

  configured_jwks_url = os.getenv("SUPABASE_JWT_JWKS_URL", "").strip()
  if configured_jwks_url:
    jwks_url = normalize_url_for_runtime(configured_jwks_url)
  else:
    parsed = urlparse(issuer)
    base_issuer = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
    jwks_url = normalize_url_for_runtime(f"{base_issuer}/.well-known/jwks.json")

  signing_key = jwt.PyJWKClient(jwks_url).get_signing_key_from_jwt(token).key

  return jwt.decode(
      token,
      signing_key,
      algorithms=[algorithm],
      audience=audience,
      issuer=issuer,
      options={"require": ["sub", "exp", "iss"]},
  )
  
