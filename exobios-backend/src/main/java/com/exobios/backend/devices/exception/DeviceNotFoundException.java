package com.exobios.backend.devices.exception;

import com.exobios.backend.common.exception.ResourceNotFoundException;

import java.util.UUID;

public class DeviceNotFoundException extends ResourceNotFoundException {

    public DeviceNotFoundException(UUID id) {
        super("Device", id);
    }
}
