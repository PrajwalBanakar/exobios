package com.exobios.backend.users.mapper;

import com.exobios.backend.users.dto.UserDto;
import com.exobios.backend.users.entity.User;
import org.mapstruct.Mapper;
import org.mapstruct.MappingConstants;
import org.mapstruct.ReportingPolicy;

import java.util.List;

@Mapper(
        componentModel = MappingConstants.ComponentModel.SPRING,
        unmappedTargetPolicy = ReportingPolicy.ERROR
)
public interface UserMapper {

    // passwordHash is in User (source) but not in UserDto (target) — MapStruct ignores it automatically.
    UserDto toDto(User user);

    List<UserDto> toDtoList(List<User> users);
}
