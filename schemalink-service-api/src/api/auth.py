from fastapi import HTTPException, status


def check_token(headers, auth_tokens):
    if headers.get("Authorization").split(" ")[1] not in auth_tokens:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token is wrong!")
