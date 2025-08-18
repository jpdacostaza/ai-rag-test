# Middleware - Complete Request Processing Pipeline

## Security Middleware (`middleware/security_middleware.py`)

### CORS Configuration
**Purpose**: Cross-Origin Resource Sharing configuration for web client compatibility.

**Implementation Details:**
- **Allowed Origins**: Configurable origin validation with wildcard support
- **Allowed Methods**: GET, POST, PUT, DELETE, OPTIONS for full REST API support
- **Allowed Headers**: Content-Type, Authorization, X-User-ID, X-Correlation-ID
- **Credentials Support**: Enable for authentication cookie handling

**Security Features:**
- **Origin Validation**: Strict origin checking with configurable allowlist
- **Method Restriction**: Only explicitly allowed HTTP methods accepted
- **Header Control**: Limited header exposure for security
- **Preflight Handling**: Proper OPTIONS request handling for complex requests

### Content Security Policy (CSP)
**Purpose**: Prevent XSS attacks and control resource loading.

**Policy Configuration:**
```
default-src 'self';
script-src 'self' 'unsafe-inline';
style-src 'self' 'unsafe-inline';
img-src 'self' data: https:;
connect-src 'self' https:;
font-src 'self';
frame-ancestors 'none';
```

**Features:**
- **Script Control**: Prevent unauthorized script execution
- **Style Security**: Control CSS source validation
- **Image Policy**: Allow self-hosted and secure external images
- **Connection Control**: Restrict AJAX/fetch destinations
- **Frame Protection**: Prevent clickjacking attacks

### Security Headers
**Purpose**: Comprehensive security header injection for request hardening.

**Headers Applied:**
- **X-Frame-Options**: `DENY` - Prevent page embedding
- **X-Content-Type-Options**: `nosniff` - Prevent MIME type sniffing
- **X-XSS-Protection**: `1; mode=block` - Enable XSS filtering
- **Strict-Transport-Security**: `max-age=31536000; includeSubDomains` - Force HTTPS
- **Referrer-Policy**: `strict-origin-when-cross-origin` - Control referrer information
- **Permissions-Policy**: Restrict browser feature access

### Request Validation
**Purpose**: Input validation and sanitization at middleware level.

**Validation Features:**
- **Size Limits**: Request body size validation (configurable)
- **Content Type**: MIME type validation for uploads
- **Rate Limiting**: Request frequency control per client
- **IP Filtering**: Optional IP allowlist/blocklist support

## Performance Middleware (`middleware/performance_middleware.py`)

### Request Timing
**Purpose**: Comprehensive request performance monitoring and optimization.

**Metrics Collected:**
- **Total Request Time**: End-to-end request processing duration
- **Database Query Time**: Individual and aggregate database operation timing
- **External API Time**: Third-party service call duration
- **Memory Operations**: Memory system interaction timing
- **Cache Performance**: Cache hit/miss ratios and response times

**Implementation Details:**
```python
async def performance_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Inject timing context
    request.state.timing_context = TimingContext()
    
    response = await call_next(request)
    
    # Calculate and log metrics
    total_time = time.time() - start_time
    await log_performance_metrics(request, total_time)
    
    return response
```

### Resource Monitoring
**Purpose**: Real-time resource usage tracking and alerting.

**Monitored Resources:**
- **Memory Usage**: Current and peak memory consumption
- **CPU Utilization**: Request processing CPU usage
- **Connection Pools**: Database and external service connection health
- **Async Task Queues**: Background task queue depths

### Performance Headers
**Purpose**: Performance information injection for debugging and monitoring.

**Headers Added:**
- **X-Response-Time**: Request processing duration in milliseconds
- **X-Database-Queries**: Number of database queries executed
- **X-Cache-Status**: HIT/MISS cache status indicator
- **X-Service-Version**: Application version for debugging

### Optimization Features
**Purpose**: Automatic performance optimization based on request patterns.

**Optimizations:**
- **Response Compression**: Automatic gzip compression for large responses
- **Static Resource Caching**: Long-term caching headers for static content
- **Connection Pooling**: Efficient database connection management
- **Async Optimization**: Concurrent operation optimization

## Rate Limiting Middleware (`middleware/rate_limit_middleware.py`)

### Token Bucket Algorithm
**Purpose**: Fair and efficient rate limiting using token bucket implementation.

**Algorithm Details:**
- **Bucket Capacity**: Maximum tokens per time window (configurable)
- **Refill Rate**: Tokens added per second (configurable)
- **Token Cost**: Tokens consumed per request (request-specific)
- **Burst Handling**: Allow brief bursts up to bucket capacity

**Implementation:**
```python
class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
```

### Client Identification
**Purpose**: Accurate client identification for rate limiting.

**Identification Methods:**
- **IP Address**: Primary identification method with proxy support
- **User ID**: Authenticated user rate limiting
- **API Key**: Service-specific rate limiting
- **Session ID**: Session-based rate limiting

**Proxy Support:**
- **X-Forwarded-For**: Proxy header parsing
- **X-Real-IP**: Direct IP extraction
- **Cloudflare Support**: CF-Connecting-IP header handling

### Rate Limit Types
**Purpose**: Multiple rate limiting strategies for different use cases.

**Global Rate Limits:**
- **Requests per Second**: 100 requests/second default
- **Burst Capacity**: 200 requests burst allowance
- **Sliding Window**: 1-hour sliding window tracking

**Endpoint-Specific Limits:**
- **Chat Completions**: 60 requests/minute for LLM endpoints
- **Memory Operations**: 120 requests/minute for memory APIs
- **File Uploads**: 10 uploads/hour with size considerations
- **Search Operations**: 100 searches/minute

**User-Tier Limits:**
- **Free Tier**: Basic rate limits with lower thresholds
- **Premium Tier**: Higher limits for authenticated users
- **Admin Tier**: Significantly relaxed limits for administrators

### Rate Limit Headers
**Purpose**: Client communication of rate limit status.

**Headers Provided:**
- **X-RateLimit-Limit**: Maximum requests allowed in window
- **X-RateLimit-Remaining**: Remaining requests in current window
- **X-RateLimit-Reset**: UTC timestamp when limit resets
- **X-RateLimit-Retry-After**: Seconds to wait before retry (when exceeded)

### Distributed Rate Limiting
**Purpose**: Rate limiting across multiple application instances.

**Redis Integration:**
- **Shared Counters**: Distributed counters in Redis
- **Atomic Operations**: Lua scripts for atomic increment/check operations
- **TTL Management**: Automatic counter expiration
- **Failover Handling**: Local fallback when Redis unavailable

## Gateway Middleware (aiohttp-based)

### IP Filtering
**Purpose**: Network-level access control and traffic filtering.

**Features:**
- **IP Allowlist**: Permitted IP addresses and ranges
- **IP Blocklist**: Blocked IP addresses and ranges
- **CIDR Support**: Network range filtering
- **Dynamic Updates**: Runtime IP list updates without restart

### Rate Limiting with Burst Control
**Purpose**: Gateway-level rate limiting with burst tolerance.

**Implementation:**
- **Burst Control**: Allow temporary traffic spikes
- **Sliding Windows**: More accurate rate measurement
- **Distributed Tracking**: Cross-instance rate limit coordination
- **Automatic Recovery**: Rate limit recovery after violations

### JWT Authentication (Demo)
**Purpose**: Basic JWT token validation for demonstration purposes.

**Note**: Simplified implementation for demonstration. Production systems should use proper JWT libraries with full validation.

**Features:**
- **Token Extraction**: Bearer token extraction from headers
- **Basic Validation**: Signature and expiration checking
- **Claim Extraction**: User and permission claim processing
- **Error Handling**: Proper authentication error responses

### Input Validation
**Purpose**: Gateway-level input sanitization and validation.

**Validation Targets:**
- **Headers**: Header format and content validation
- **Body**: Request body structure and content validation
- **Query Parameters**: Query string validation and sanitization
- **Path Parameters**: URL path component validation

### Circuit Breaker
**Purpose**: Prevent cascade failures and provide service protection.

**Circuit States:**
- **Closed**: Normal operation with success/failure tracking
- **Open**: Failing fast to prevent cascade failures
- **Half-Open**: Testing recovery with limited traffic

**Configuration:**
- **Failure Threshold**: Number of failures before opening circuit
- **Timeout Period**: Duration to keep circuit open
- **Success Threshold**: Successes needed to close circuit

### Security Headers
**Purpose**: Gateway-level security header injection.

**Headers Applied:**
- **Security Headers**: Comprehensive security header suite
- **CORS Headers**: Cross-origin request handling
- **Cache Control**: Appropriate caching directives
- **Content Headers**: Content type and encoding headers

### Incident Logging
**Purpose**: Security incident tracking and alerting.

**Logged Events:**
- **Authentication Failures**: Failed login attempts
- **Rate Limit Violations**: Traffic threshold breaches
- **Security Violations**: Suspicious request patterns
- **Circuit Breaker Events**: Service availability issues

### Periodic Cleanup
**Purpose**: Resource management and maintenance tasks.

**Cleanup Tasks:**
- **Rate Limit Counters**: Expired counter cleanup
- **Circuit Breaker State**: State reset for recovered services
- **Log Rotation**: Old log file management
- **Cache Cleanup**: Expired cache entry removal

## Logging Middleware (`core/unified_logging.py`)

### Correlation ID Management
**Purpose**: Request tracing across distributed components.

**Implementation:**
- **ID Generation**: UUID4-based correlation IDs for unique tracking
- **Header Injection**: X-Correlation-ID header management
- **Context Propagation**: Correlation ID propagation through all service calls
- **Thread Safety**: Async-safe correlation ID context management

### Structured Logging
**Purpose**: Machine-readable log format for monitoring and analysis.

**Log Structure:**
```json
{
  "timestamp": "2025-01-09T10:30:00Z",
  "level": "INFO",
  "message": "Request processed successfully",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user123",
  "endpoint": "/v1/chat/completions",
  "method": "POST",
  "status_code": 200,
  "response_time_ms": 150,
  "request_size": 1024,
  "response_size": 2048
}
```

### Request/Response Logging
**Purpose**: Comprehensive request and response tracking for debugging and monitoring.

**Logged Information:**
- **Request Details**: Method, path, headers, query parameters, body size
- **Response Details**: Status code, headers, body size, processing time
- **Error Information**: Exception details, stack traces, error correlation
- **Security Events**: Authentication failures, rate limit violations

## Error Handling Middleware (`core/error_handler.py`)

### Exception Mapping
**Purpose**: Standardized error response generation from Python exceptions.

**Exception Mappings:**
- **ValidationError**: 400 Bad Request with validation details
- **AuthenticationError**: 401 Unauthorized with authentication requirements
- **AuthorizationError**: 403 Forbidden with permission details
- **NotFoundError**: 404 Not Found with resource information
- **RateLimitError**: 429 Too Many Requests with retry information
- **ServiceUnavailableError**: 503 Service Unavailable with retry guidance

### Error Response Format
**Purpose**: Consistent error response structure across all endpoints.

**Standard Error Response:**
```json
{
  "error": {
    "type": "ValidationError",
    "message": "User-friendly error description",
    "details": "Technical error details for debugging",
    "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2025-01-09T10:30:00Z",
    "path": "/v1/chat/completions",
    "method": "POST",
    "status_code": 400
  },
  "success": false
}
```

### Circuit Breaker Integration
**Purpose**: Prevent cascade failures with automatic circuit breaking.

**Features:**
- **Service Health Tracking**: Monitor downstream service health
- **Automatic Failover**: Switch to fallback responses during outages
- **Recovery Detection**: Automatic recovery when services return
- **Configurable Thresholds**: Customizable failure and recovery thresholds

## Configuration and Best Practices

### Environment-Specific Configuration
**Purpose**: Optimized middleware configuration for different deployment environments.

**Development Environment:**
- **Relaxed Security**: Reduced security for easier development
- **Verbose Logging**: Detailed debugging information
- **No Rate Limiting**: Unlimited requests for testing

**Staging Environment:**
- **Production-Like**: Similar to production configuration
- **Enhanced Debugging**: Additional debugging capabilities
- **Load Testing**: Performance testing configuration

**Production Environment:**
- **Strict Security**: Maximum security configuration
- **Optimized Performance**: Performance-tuned settings
- **Comprehensive Monitoring**: Full monitoring and alerting

### Middleware Stack Order
**Purpose**: Proper middleware execution order for optimal functionality.

**Execution Order:**
1. **CORS Middleware**: Handle preflight requests first
2. **Security Middleware**: Apply security headers and validation
3. **Rate Limiting**: Enforce rate limits before processing
4. **Logging Middleware**: Start request logging and correlation
5. **Performance Middleware**: Begin performance monitoring
6. **Authentication**: Validate user credentials and permissions
7. **Application Logic**: Execute business logic
8. **Error Handling**: Catch and format errors
9. **Response Middleware**: Final response processing
