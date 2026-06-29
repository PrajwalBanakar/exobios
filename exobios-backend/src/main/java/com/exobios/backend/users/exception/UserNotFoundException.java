package com.exobios.backend.users.exception;

import com.exobios.backend.common.exception.ResourceNotFoundException;

import java.util.UUID;

public class UserNotFoundException extends ResourceNotFoundException {

    public UserNotFoundException(UUID id) {
        super("User", id);
    }

    public UserNotFoundException(String message) {
        super(message);
    }
}
