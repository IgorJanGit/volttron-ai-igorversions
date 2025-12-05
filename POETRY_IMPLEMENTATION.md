# VOLTTRON Library Installation - Poetry Implementation

## Summary

The implementation has been updated to use the **official VOLTTRON-core Poetry-based method** as requested in your comment referencing [eclipse-volttron/volttron-core#221](https://github.com/eclipse-volttron/volttron-core/issues/221).

## What Changed

### Previous Implementation
- Used `pip install` directly
- Simple but not aligned with official VOLTTRON-core approach

### Current Implementation (Official Method)
- Uses `poetry add <library>` in `$VOLTTRON_HOME` 
- Follows the official VOLTTRON-core implementation from issue #221
- Tracks dependencies in `pyproject.toml`
- Falls back to pip if Poetry is not installed

## How It Works

The implementation mimics the official `vctl install-lib` command:

```bash
cd $VOLTTRON_HOME
poetry add volttron-lib-modbustk-driver
```

This ensures:
1. ✅ Dependencies are tracked in `pyproject.toml`
2. ✅ Poetry manages version conflicts automatically
3. ✅ Compatible with modular VOLTTRON (v2.0.0rc0+)
4. ✅ Proper dependency resolution

## Features

### Poetry Integration
- Automatically initializes `pyproject.toml` if it doesn't exist
- Detects current Python version for dependency constraints
- Runs `poetry add` in VOLTTRON_HOME

### Pip Fallback
- If Poetry is not installed, falls back to `pip install`
- Provides clear message suggesting Poetry installation
- Ensures users can still install libraries

### Security
- Validates library names to prevent shell injection
- Only allows alphanumeric characters, hyphens, underscores, and dots
- Cross-platform compatible (uses `shutil.which`)

## Usage Examples

### Via AI Chat (Natural Language)
```
"install library volttron-lib-modbustk-driver"
"vctl install-lib volttron-lib-bacnet-driver"
"Can you install the fake driver library?"
```

### Direct Function Call
```python
from chat_app.volttron_commands import vctl_install_lib

# Install with Poetry (official method)
result = vctl_install_lib('volttron-lib-modbustk-driver')
```

## Requirements

### Recommended (Official Method)
```bash
pip install poetry
```

### Minimum (Fallback)
- Python 3.8+
- Virtual environment with pip

## Installation Flow

1. **Check for Poetry** - Uses `shutil.which('poetry')`
2. **If Poetry exists:**
   - Check for `$VOLTTRON_HOME/pyproject.toml`
   - Initialize if needed (with current Python version)
   - Run `poetry add <library>`
   - Track in pyproject.toml
3. **If Poetry missing:**
   - Use pip as fallback
   - Suggest installing Poetry
   - Still install the library successfully

## Benefits Over Previous Implementation

| Feature | Previous (pip) | Current (Poetry) |
|---------|---------------|------------------|
| **Dependency tracking** | No | Yes (pyproject.toml) |
| **Version management** | Manual | Automatic (Poetry) |
| **VOLTTRON compatibility** | Works | Official method |
| **Fallback option** | N/A | pip (if Poetry missing) |
| **Security validation** | Basic | Enhanced |
| **Cross-platform** | Limited | Full support |

## Testing

All tests pass:
- ✅ Syntax validation
- ✅ Import tests
- ✅ Function signature tests
- ✅ AI integration tests
- ✅ Security scan (CodeQL - No issues)

## References

- **Primary**: [eclipse-volttron/volttron-core#221](https://github.com/eclipse-volttron/volttron-core/issues/221) - Add vctl install-lib
- **Background**: [eclipse-volttron/volttron-core#141](https://github.com/eclipse-volttron/volttron-core/issues/141) - Poetry integration discussion

## Commit History

1. Initial pip-based implementation
2. Updated to Poetry-based (official method) - commit 2e48a4b
3. Code review improvements (security, cross-platform) - commit a176ba8

## Next Steps

The implementation is ready to use! You can:

1. **Install Poetry** (recommended for official method):
   ```bash
   pip install poetry
   ```

2. **Use the feature**:
   ```
   "install library volttron-lib-modbustk-driver"
   ```

3. **Libraries are tracked** in `$VOLTTRON_HOME/pyproject.toml`

## Support

The implementation now fully aligns with the official VOLTTRON-core approach and provides the same functionality as the `vctl install-lib` command from issue #221, while working even when VOLTTRON is not running.
