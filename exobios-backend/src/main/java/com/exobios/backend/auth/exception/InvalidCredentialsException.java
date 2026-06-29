package com.exobios.backend.auth.exception;

import com.exobios.backend.common.exception.UnauthorizedException;

public class InvalidCredentialsException extends UnauthorizedException {

    public InvalidCredentialsException() {
        super("Invalid phone number or password");
    }
}
