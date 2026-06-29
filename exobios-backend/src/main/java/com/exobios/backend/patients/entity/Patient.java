package com.exobios.backend.patients.entity;

import com.exobios.backend.common.entity.BaseEntity;
import com.exobios.backend.patients.entity.enums.Gender;
import com.exobios.backend.patients.entity.enums.PatientStatus;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EntityListeners;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDate;
import java.util.UUID;

@Entity
@Table(name = "patients")
@EntityListeners(AuditingEntityListener.class)
@Getter
@Setter
@NoArgsConstructor
public class Patient extends BaseEntity {

    @Column(name = "patient_code", unique = true, nullable = false, length = 20)
    private String patientCode;

    @Column(name = "name", nullable = false, length = 100)
    private String name;

    @Column(name = "age")
    private Short age;

    @Enumerated(EnumType.STRING)
    @Column(name = "gender", length = 10)
    private Gender gender;

    @Column(name = "dob")
    private LocalDate dob;

    @Column(name = "phone", length = 20)
    private String phone;

    @Column(name = "address", columnDefinition = "TEXT")
    private String address;

    @Column(name = "village", length = 100)
    private String village;

    @Column(name = "district", length = 100)
    private String district;

    @Column(name = "state", length = 100)
    private String state;

    @Column(name = "aadhaar_number", length = 12)
    private String aadhaarNumber;

    @Column(name = "asha_worker_id", nullable = false)
    private UUID ashaWorkerId;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 20)
    private PatientStatus status = PatientStatus.ACTIVE;
}
