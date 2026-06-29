package com.exobios.backend.patients.mapper;

import com.exobios.backend.patients.dto.PatientDto;
import com.exobios.backend.patients.entity.Patient;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.MappingConstants;
import org.mapstruct.Named;
import org.mapstruct.ReportingPolicy;

import java.util.List;

@Mapper(componentModel = MappingConstants.ComponentModel.SPRING,
        unmappedTargetPolicy = ReportingPolicy.ERROR)
public interface PatientMapper {

    // @Named on maskAadhaar prevents MapStruct from treating it as a general-purpose
    // String→String converter (which would corrupt name, patientCode, phone, etc.).
    // It is only invoked when explicitly referenced via qualifiedByName.
    @Mapping(target = "maskedAadhaar", source = "aadhaarNumber", qualifiedByName = "maskAadhaar")
    @Mapping(target = "age", expression = "java(patient.getAge() != null ? patient.getAge().intValue() : null)")
    PatientDto toDto(Patient patient);

    List<PatientDto> toDtoList(List<Patient> patients);

    @Named("maskAadhaar")
    default String maskAadhaar(String aadhaar) {
        if (aadhaar == null || aadhaar.isBlank() || aadhaar.length() != 12) return null;
        return "XXXX-XXXX-" + aadhaar.substring(8);
    }
}
