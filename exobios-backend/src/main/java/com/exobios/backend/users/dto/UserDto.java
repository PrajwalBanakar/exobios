package com.exobios.backend.users.dto;

import com.exobios.backend.users.entity.enums.Role;
import com.exobios.backend.users.entity.enums.UserStatus;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.UUID;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserDto {

    private UUID id;
    private String ashaId;
    private String phone;
    private String name;
    private Role role;
    private String area;
    private String district;
    private String state;
    private UserStatus status;
    private Instant lastLoginAt;
    private Instant createdAt;
    private Instant updatedAt;
}
