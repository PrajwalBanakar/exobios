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
public class ExaminationFindingDto {
    private UUID   id;
    private String generalAppearance;
    private String consciousness;
    private String edema;
    private String skin;
    private String respiratory;
    private String cardiovascular;
    private String abdominal;
    private String neurological;
}
