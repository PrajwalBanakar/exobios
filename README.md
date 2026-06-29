
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
│     │  │        └─ security
│     │  │           ├─ jwt
│     │  │           │  ├─ JwtAuthenticationFilter.class
│     │  │           │  ├─ JwtProperties.class
│     │  │           │  └─ JwtTokenProvider.class
│     │  │           ├─ JwtAccessDeniedHandler.class
│     │  │           ├─ JwtAuthenticationEntryPoint.class
│     │  │           ├─ UserDetailsServiceImpl.class
│     │  │           └─ UserPrincipal.class
│     │  └─ db
│     │     └─ migration
│     ├─ generated-sources
│     │  └─ annotations
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