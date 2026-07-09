package com.exobios.backend.testsupport;

import com.exobios.backend.config.SecurityConfig;
import com.exobios.backend.security.JwtAccessDeniedHandler;
import com.exobios.backend.security.JwtAuthenticationEntryPoint;
import com.exobios.backend.security.UserDetailsServiceImpl;
import com.exobios.backend.security.jwt.JwtTokenProvider;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.test.web.servlet.MockMvc;

/**
 * Shared setup for every {@code @WebMvcTest} controller test.
 *
 * Importing the real {@link SecurityConfig} (rather than disabling security for the
 * slice) means these tests exercise the actual filter chain: real JWT parsing via
 * {@link JwtTokenProvider}, and real {@code @PreAuthorize} enforcement via
 * {@code @EnableMethodSecurity}. {@link WebMvcTestSecurityConfig} supplies the two
 * {@code @ConfigurationProperties} beans {@code SecurityConfig} needs that a
 * {@code @WebMvcTest} slice wouldn't otherwise bind.
 *
 * {@link UserDetailsServiceImpl} is mocked purely to satisfy {@code SecurityConfig}'s
 * {@code DaoAuthenticationProvider} bean — it needs a {@code UserRepository}-backed
 * service that isn't available in a web-only test slice, but none of these tests
 * exercise username/password login (that's covered by {@code AuthServiceTest}), so a
 * bare mock is sufficient.
 *
 * {@link JwtTokenProvider}, {@link JwtAuthenticationEntryPoint}, and
 * {@link JwtAccessDeniedHandler} are plain {@code @Component}s that a {@code @WebMvcTest}
 * slice does not scan by default (it only auto-detects controllers/converters/security
 * filters), so they must be imported explicitly alongside {@code SecurityConfig} for its
 * bean graph to resolve.
 */
@Import({
        SecurityConfig.class,
        WebMvcTestSecurityConfig.class,
        JwtTokenProvider.class,
        JwtAuthenticationEntryPoint.class,
        JwtAccessDeniedHandler.class,
})
public abstract class AbstractControllerTest {

    @MockBean
    protected UserDetailsServiceImpl userDetailsService;

    @Autowired
    protected MockMvc mockMvc;

    @Autowired
    protected ObjectMapper objectMapper;

    @Autowired
    protected JwtTokenProvider jwtTokenProvider;
}
