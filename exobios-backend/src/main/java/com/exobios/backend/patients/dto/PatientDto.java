package com.exobios.backend.patients.dto;

import com.exobios.backend.patients.entity.enums.Gender;
import com.exobios.backend.patients.entity.enums.PatientStatus;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.time.LocalDate;
import java.util.UUID;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PatientDto {

    private UUID          id;
    private String        patientCode;
    private String        name;
    private Integer       age;           // Short entity field widened to Integer for API ergonomics
    private Gender        gender;
    private LocalDate     dob;
    private String        phone;
    private String        address;
    private String        village;
    private String        district;
    private String        state;
    private String        maskedAadhaar; // "XXXX-XXXX-1234" — raw Aadhaar is never returned
    private UUID          ashaWorkerId;
    private PatientStatus status;
    private Instant       createdAt;
    private Instant       updatedAt;
}
