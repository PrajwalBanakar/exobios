package com.exobios.backend.patients.dto;

import com.exobios.backend.patients.entity.enums.Gender;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDate;

@Getter
@Setter
@NoArgsConstructor
public class UpdatePatientRequest {

    @NotBlank(message = "Patient name is required")
    @Size(max = 100, message = "Name must not exceed 100 characters")
    private String name;

    @Min(value = 0,   message = "Age must be 0 or greater")
    @Max(value = 120, message = "Age must not exceed 120")
    private Integer age;

    private Gender gender;

    private LocalDate dob;

    @Pattern(regexp = "^[6-9]\\d{9}$", message = "Enter a valid 10-digit Indian mobile number")
    private String phone;

    private String address;

    @Size(max = 100)
    private String village;

    @Size(max = 100)
    private String district;

    @Size(max = 100)
    private String state;

    /** Pass null to leave Aadhaar unchanged; pass an empty string to clear it. */
    @Pattern(regexp = "^(\\d{12})?$", message = "Aadhaar number must be exactly 12 digits")
    private String aadhaarNumber;
}
