package com.exobios.backend.devices.mapper;

import com.exobios.backend.devices.dto.DeviceDto;
import com.exobios.backend.devices.entity.Device;
import org.mapstruct.Mapper;
import org.mapstruct.MappingConstants;
import org.mapstruct.ReportingPolicy;

import java.util.List;

@Mapper(componentModel = MappingConstants.ComponentModel.SPRING,
        unmappedTargetPolicy = ReportingPolicy.ERROR)
public interface DeviceMapper {

    DeviceDto toDto(Device device);

    List<DeviceDto> toDtoList(List<Device> devices);
}
