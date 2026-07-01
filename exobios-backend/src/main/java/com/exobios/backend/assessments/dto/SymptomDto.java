package com.exobios.backend.assessments.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.UUID;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SymptomDto {
    private UUID   id;
    private String name;
    private String duration;
    private String severity;
    private String remarks;
}
