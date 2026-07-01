package com.exobios.backend.sos.dto;

import com.exobios.backend.sos.entity.enums.SosStatus;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class UpdateSosStatusRequest {

    @NotNull(message = "status is required")
    private SosStatus status;
}
