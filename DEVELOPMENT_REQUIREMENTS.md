# Development Requirements

## Critical Tools for API Integrations

This project integrates with external APIs (Jupiter, Solana, etc.) that frequently update their endpoints, authentication methods, and data formats. To maintain reliable integrations, the following tools are **MANDATORY** for development:

### 🔧 Required MCP Tools

#### 1. Jupiter API Documentation
- **Tool**: `mcp_jup_doc`
- **Purpose**: Access Jupiter's official API documentation
- **Usage**: `mcp_jup_doc query "Jupiter API v2 endpoints"`
- **Impact**: Without this, API migrations (like v6→v2) cannot be detected

#### 2. Jupiter API Specification Queries
- **Tool**: `jup_doc_query_docs_filesystem_jupiter`
- **Purpose**: Query Jupiter's API specifications and endpoint definitions
- **Usage**: `jup_doc_query_docs_filesystem_jupiter "find /swap -name '*api*'"`
- **Impact**: Without this, endpoint changes cannot be properly tracked

### ⚠️ Consequences of Missing Tools

**Real-world example (July 4, 2026)**:
- Jupiter migrated from API v6 to v2
- Old endpoints (`/v6/quote`) stopped working
- New endpoints (`/swap/v2/quote`) were not documented in public docs
- **Result**: 4+ hours wasted troubleshooting 404 errors
- **Root cause**: No access to MCP tools to check official documentation

### 📋 Development Checklist

Before starting development on API integrations:

1. ✅ Verify `mcp_jup_doc` is available and configured
2. ✅ Verify `jup_doc_query_docs_filesystem_jupiter` is available
3. ✅ Test MCP connectivity: `mcp_jup_doc ping`
4. ✅ Check for API migration announcements
5. ✅ Verify current endpoint versions

### 🔗 Reference Documentation

- [Jupiter Developer Portal](https://developers.jup.ag/)
- [Jupiter Swap API v2](https://developers.jup.ag/swap/index)
- [Migration Guide](https://developers.jup.ag/docs/portal/migration)

### 📝 Troubleshooting

**Symptom**: API endpoints returning 404 errors

**Diagnosis**:
1. Check if MCP tools are available
2. Query current API version: `jup_doc_query_docs_filesystem_jupiter "cat /swap/index.mdx | grep 'swap/v'"`
3. Compare with current implementation

**Solution**:
1. Update endpoints to match official documentation
2. Test connectivity
3. Update codebase
4. Add test coverage

### 🎯 Best Practices

1. **Always check MCP docs first** before troubleshooting API issues
2. **Document API versions** in code comments with references
3. **Add regression tests** for critical API endpoints
4. **Monitor API changelogs** via MCP tools

```python
# GOOD EXAMPLE: Documented API version with reference
# Jupiter Swap API v2 - https://developers.jup.ag/swap/index
QUOTE_ENDPOINT = "/swap/v2/quote"  # Confirmed via mcp_jup_doc 2026-07-04
```

### 📚 Maintenance

Regularly verify MCP tool availability:
- Monthly: Test basic queries
- Quarterly: Review API changelogs
- Before major updates: Full endpoint verification

**Last verified**: 2026-07-04
**Last API migration**: v6 → v2 (2026-07-04)
**Current stable version**: Swap API v2
