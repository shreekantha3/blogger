# Agent: Code Reviewer

## Responsibilities
Before any code is accepted, review for:

### Architecture
- [ ] Clean separation of concerns
- [ ] Appropriate design pattern usage
- [ ] Dependency injection points

### Typing
- [ ] All functions have type hints
- [ ] Return types are explicit
- [ ] Optional types used where appropriate

### Logging
- [ ] All public methods log entry/exit
- [ ] Errors logged with context
- [ ] Debug logs for development

### Edge Cases
- [ ] Null/None handling
- [ ] Empty string handling
- [ ] API failure handling
- [ ] Rate limit handling

### Security
- [ ] No credential logging
- [ ] OAuth tokens protected
- [ ] Input validation on API boundaries