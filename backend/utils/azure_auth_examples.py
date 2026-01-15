"""
Azure Authentication Examples for LangChain AzureChatOpenAI

Official LangChain documentation approaches for Azure AD authentication.
"""

from azure.identity import (
    DefaultAzureCredential,
    ManagedIdentityCredential,
    AzureCliCredential,
    ChainedTokenCredential,
    get_bearer_token_provider
)
from langchain_openai import AzureChatOpenAI
import os


# ==========================================
# 1. DefaultAzureCredential (Empfohlen für Produktion)
# ==========================================
# Versucht automatisch verschiedene Auth-Methoden in dieser Reihenfolge:
# - EnvironmentCredential
# - ManagedIdentityCredential
# - AzureCliCredential
# - usw.

def create_model_with_default_credential():
    """Production-ready: Funktioniert in Azure und lokal mit az login"""
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://cognitiveservices.azure.com/.default"
    )
    
    return AzureChatOpenAI(
        model=os.getenv("AZURE_DEPLOYMENT_NAME"),
        api_version=os.getenv("AZURE_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_ENDPOINT_URL"),
        azure_ad_token_provider=token_provider
    )


# ==========================================
# 2. ManagedIdentityCredential (Für Azure-Ressourcen)
# ==========================================
# Nur in Azure-Umgebungen (VM, App Service, Container, etc.)

def create_model_with_managed_identity():
    """Nur für Azure-Ressourcen mit Managed Identity"""
    token_provider = get_bearer_token_provider(
        ManagedIdentityCredential(),
        "https://cognitiveservices.azure.com/.default"
    )
    
    return AzureChatOpenAI(
        model=os.getenv("AZURE_DEPLOYMENT_NAME"),
        api_version=os.getenv("AZURE_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_ENDPOINT_URL"),
        azure_ad_token_provider=token_provider
    )


# ==========================================
# 3. AzureCliCredential (Für lokale Entwicklung)
# ==========================================
# Nutzt `az login` Token - gut für lokales Debugging

def create_model_with_cli_credential():
    """Für lokale Entwicklung nach `az login`"""
    token_provider = get_bearer_token_provider(
        AzureCliCredential(),
        "https://cognitiveservices.azure.com/.default"
    )
    
    return AzureChatOpenAI(
        model=os.getenv("AZURE_DEPLOYMENT_NAME"),
        api_version=os.getenv("AZURE_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_ENDPOINT_URL"),
        azure_ad_token_provider=token_provider
    )


# ==========================================
# 4. ChainedTokenCredential (Custom Fallback-Kette)
# ==========================================
# Definiere eigene Reihenfolge der Auth-Versuche

def create_model_with_chained_credential():
    """Custom Fallback: Erst Managed Identity, dann CLI"""
    credential = ChainedTokenCredential(
        ManagedIdentityCredential(),  # Versuche erst Managed Identity
        AzureCliCredential()           # Falls fehlschlägt: CLI
    )
    
    token_provider = get_bearer_token_provider(
        credential,
        "https://cognitiveservices.azure.com/.default"
    )
    
    return AzureChatOpenAI(
        model=os.getenv("AZURE_DEPLOYMENT_NAME"),
        api_version=os.getenv("AZURE_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_ENDPOINT_URL"),
        azure_ad_token_provider=token_provider
    )


# ==========================================
# 5. API Key (Legacy - nicht empfohlen)
# ==========================================
def create_model_with_api_key():
    """Legacy-Methode mit API Key - nicht empfohlen für Produktion"""
    return AzureChatOpenAI(
        model=os.getenv("AZURE_DEPLOYMENT_NAME"),
        api_version=os.getenv("AZURE_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_ENDPOINT_URL"),
        api_key=os.getenv("AZURE_API_KEY")  # ⚠️ Unsicher
    )


# ==========================================
# Best Practice für dein Projekt
# ==========================================
def create_production_ready_model():
    """
    Empfohlener Ansatz für Produktion:
    - Funktioniert in Azure (Managed Identity)
    - Funktioniert lokal (az login)
    - Keine API Keys im Code
    """
    endpoint = os.getenv("AZURE_ENDPOINT_URL", "https://gpt4-se-dev.openai.azure.com/")
    model = os.getenv("AZURE_DEPLOYMENT_NAME", "GPT-4o")
    api_version = os.getenv("AZURE_API_VERSION", "2025-01-01-preview")
    
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://cognitiveservices.azure.com/.default"
    )
    
    return AzureChatOpenAI(
        model=model,
        api_version=api_version,
        azure_endpoint=endpoint,
        azure_ad_token_provider=token_provider,
        temperature=0.3  # Optional: Model-Parameter
    )


# ==========================================
# Debugging: Token manuell abrufen
# ==========================================
def test_token_retrieval():
    """Test ob Token erfolgreich abgerufen werden kann"""
    try:
        credential = DefaultAzureCredential()
        token = credential.get_token("https://cognitiveservices.azure.com/.default")
        print(f"✓ Token erfolgreich abgerufen")
        print(f"Expires: {token.expires_on}")
        return True
    except Exception as e:
        print(f"✗ Token-Fehler: {e}")
        return False


if __name__ == "__main__":
    # Test Token-Abruf
    print("Testing Azure AD Token...")
    test_token_retrieval()
