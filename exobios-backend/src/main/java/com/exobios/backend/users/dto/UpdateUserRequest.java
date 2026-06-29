package com.exobios.backend.users.dto;

import com.exobios.backend.users.entity.enums.Role;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class UpdateUserRequest {

    @NotBlank(message = "Name is required")
    @Size(max = 100, message = "Name must not exceed 100 characters")
    private String name;

    /** If provided, must be a valid 10-digit Indian mobile number and not already taken. */
    @Pattern(regexp = "^[6-9]\\d{9}$", message = "Enter a valid 10-digit Indian mobile number")
    private String phone;

    /** Optional — conflict-checked in service. Required when changing role to ASHA. */
    private String ashaId;

    /** If provided, updates the user's role. Changing to ASHA requires ashaId. */
    private Role role;

    private String area;
    private String district;
    private String state;
}
