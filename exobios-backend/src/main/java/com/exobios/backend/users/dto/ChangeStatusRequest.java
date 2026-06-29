package com.exobios.backend.users.dto;

import com.exobios.backend.users.entity.enums.UserStatus;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class ChangeStatusRequest {

    @NotNull(message = "Status is required")
    private UserStatus status;
}
