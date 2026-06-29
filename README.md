
```
exobios
├─ docs
│  ├─ api
│  ├─ architecture
│  ├─ database
│  └─ deployment
├─ exobios-ai
├─ exobios-backend
│  ├─ docker-compose.yml
│  ├─ Dockerfile
│  ├─ pom.xml
│  └─ target
│     ├─ classes
│     │  ├─ application-dev.yml
│     │  ├─ application-prod.yml
│     │  ├─ application.yml
│     │  ├─ com
│     │  │  └─ exobios
│     │  │     └─ backend
│     │  │        ├─ auth
│     │  │        │  ├─ controller
│     │  │        │  │  └─ AuthController.class
│     │  │        │  ├─ dto
│     │  │        │  │  ├─ LoginRequest.class
│     │  │        │  │  ├─ LoginResponse$LoginResponseBuilder.class
│     │  │        │  │  ├─ LoginResponse$UserInfo$UserInfoBuilder.class
│     │  │        │  │  ├─ LoginResponse$UserInfo.class
│     │  │        │  │  ├─ LoginResponse.class
│     │  │        │  │  ├─ RefreshTokenRequest.class
│     │  │        │  │  ├─ RefreshTokenResponse$RefreshTokenResponseBuilder.class
│     │  │        │  │  └─ RefreshTokenResponse.class
│     │  │        │  ├─ exception
│     │  │        │  │  └─ InvalidCredentialsException.class
│     │  │        │  └─ service
│     │  │        │     ├─ AuthService.class
│     │  │        │     └─ RefreshTokenService.class
│     │  │        ├─ common
│     │  │        │  ├─ constants
│     │  │        │  │  └─ AppConstants.class
│     │  │        │  ├─ dto
│     │  │        │  │  ├─ ApiResponse.class
│     │  │        │  │  ├─ ErrorResponse.class
│     │  │        │  │  └─ PageResponse.class
│     │  │        │  ├─ entity
│     │  │        │  │  └─ BaseEntity.class
│     │  │        │  ├─ enums
│     │  │        │  │  └─ ApiErrorCode.class
│     │  │        │  ├─ exception
│     │  │        │  │  ├─ BadRequestException.class
│     │  │        │  │  ├─ BusinessException.class
│     │  │        │  │  ├─ ConflictException.class
│     │  │        │  │  ├─ ForbiddenException.class
│     │  │        │  │  ├─ GlobalExceptionHandler.class
│     │  │        │  │  ├─ ResourceNotFoundException.class
│     │  │        │  │  └─ UnauthorizedException.class
│     │  │        │  └─ utils
│     │  │        │     ├─ DateUtils.class
│     │  │        │     └─ SecurityUtils.class
│     │  │        ├─ config
│     │  │        │  ├─ CorsProperties.class
│     │  │        │  ├─ JpaAuditingConfig.class
│     │  │        │  └─ SecurityConfig.class
│     │  │        ├─ ExobiosApplication.class
│     │  │        ├─ security
│     │  │        │  ├─ jwt
│     │  │        │  │  ├─ JwtAuthenticationFilter.class
│     │  │        │  │  ├─ JwtProperties.class
│     │  │        │  │  └─ JwtTokenProvider.class
│     │  │        │  ├─ JwtAccessDeniedHandler.class
│     │  │        │  ├─ JwtAuthenticationEntryPoint.class
│     │  │        │  ├─ UserDetailsServiceImpl.class
│     │  │        │  └─ UserPrincipal.class
│     │  │        └─ users
│     │  │           ├─ controller
│     │  │           │  └─ UserController.class
│     │  │           ├─ dto
│     │  │           │  ├─ ChangeStatusRequest.class
│     │  │           │  ├─ CreateUserRequest.class
│     │  │           │  ├─ UpdateUserRequest.class
│     │  │           │  ├─ UserDto$UserDtoBuilder.class
│     │  │           │  └─ UserDto.class
│     │  │           ├─ entity
│     │  │           │  ├─ enums
│     │  │           │  │  ├─ Role.class
│     │  │           │  │  └─ UserStatus.class
│     │  │           │  └─ User.class
│     │  │           ├─ exception
│     │  │           │  └─ UserNotFoundException.class
│     │  │           ├─ mapper
│     │  │           │  ├─ UserMapper.class
│     │  │           │  └─ UserMapperImpl.class
│     │  │           ├─ repository
│     │  │           │  └─ UserRepository.class
│     │  │           └─ service
│     │  │              └─ UserService.class
│     │  └─ db
│     │     └─ migration
│     │        ├─ V1__create_users_table.sql
│     │        └─ V2__seed_dev_users.sql
│     ├─ generated-sources
│     │  └─ annotations
│     │     └─ com
│     │        └─ exobios
│     │           └─ backend
│     │              └─ users
│     │                 └─ mapper
│     │                    └─ UserMapperImpl.java
│     ├─ generated-test-sources
│     │  └─ test-annotations
│     ├─ maven-status
│     │  └─ maven-compiler-plugin
│     │     ├─ compile
│     │     │  └─ default-compile
│     │     │     ├─ createdFiles.lst
│     │     │     └─ inputFiles.lst
│     │     └─ testCompile
│     │        └─ default-testCompile
│     │           ├─ createdFiles.lst
│     │           └─ inputFiles.lst
│     └─ test-classes
├─ exobios-frontend
│  ├─ index.html
│  ├─ package-lock.json
│  ├─ package.json
│  ├─ postcss.config.js
│  ├─ public
│  │  ├─ favicon.svg
│  │  ├─ icons.svg
│  │  └─ manifest.json
│  ├─ README.md
│  ├─ tailwind.config.js
│  └─ vite.config.js
└─ README.md

```