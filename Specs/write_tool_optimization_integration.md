# Write Tool Optimization Integration Specification

## Overview

This specification defines how the write tool optimization system integrates with the existing workflow, tools, and agents to provide seamless, high-performance write operations while maintaining safety and consistency.

## Integration Points

### 1. Workflow Integration

#### Step 4: Research and Design Enhancement

**Standard Process**:

```
- Use architect agent to design solution architecture
- Create detailed implementation plan
```

**Enhanced with Write Optimization**:

```
- Use architect agent to design solution architecture
- Use write-optimizer agent to analyze write patterns in design
- Create optimized write plan for implementation phase
- Identify template opportunities early in design
```

**Agent Coordination**:

```python
# Parallel execution in Step 4
async def enhanced_step_4(requirements):
    """Enhanced design phase with write optimization planning"""

    # Execute design and write planning in parallel
    design_task = Task("architect", {
        "requirements": requirements,
        "focus": "architecture_and_modules"
    })

    write_planning_task = Task("write-optimizer", {
        "anticipated_files": extract_file_list(requirements),
        "operation_type": "design_phase_planning"
    })

    # Execute in parallel
    design_result, write_plan = await asyncio.gather(
        execute_agent_task(design_task),
        execute_agent_task(write_planning_task)
    )

    # Combine results for implementation phase
    return {
        "architecture": design_result,
        "write_optimization_plan": write_plan,
        "estimated_performance_gain": write_plan.performance_estimate
    }
```

#### Step 5: Implementation Enhancement

**Standard Process**:

```
- Use builder agent to implement from specifications
- Follow the architecture design
```

**Enhanced with Write Optimization**:

```
- Use builder agent with write optimization plan
- Execute optimized write operations automatically
- Monitor and adjust write strategies during implementation
```

**Integration Strategy**:

```python
# Builder agent enhanced with write optimization
class EnhancedBuilder:
    def __init__(self):
        self.write_optimizer = WriteOptimizer()
        self.operation_tracker = OperationTracker()

    async def implement_with_optimization(self, specs, write_plan):
        """Implement code with automatic write optimization"""

        # Analyze implementation for write operations
        write_operations = self.extract_write_operations(specs)

        # Apply pre-planned optimizations
        optimized_operations = self.write_optimizer.apply_plan(
            write_operations, write_plan
        )

        # Execute with real-time optimization
        results = await self.execute_optimized_writes(optimized_operations)

        # Track performance for learning
        self.operation_tracker.record_performance(results)

        return results
```

#### Step 6: Refactor Enhancement

**Standard Process**:

```
- Use cleanup agent for ruthless simplification
- Remove unnecessary abstractions
```

**Enhanced with Write Optimization**:

```
- Use cleanup agent with write optimization analysis
- Identify file structure optimizations
- Apply template extraction during cleanup
- Optimize file organization and dependencies
```

### 2. Tool Coordination

#### Write Tool Enhancement

**Current Behavior**:

```python
# Standard Write tool usage
Write(file_path="/path/to/file.py", content="...")
```

**Enhanced Behavior**:

```python
# Automatic optimization wrapper
@write_optimization_wrapper
def enhanced_write(file_path, content):
    """Write with automatic optimization detection"""

    # Check for optimization opportunities
    optimizer = get_write_optimizer()

    if optimizer.should_optimize(file_path, content):
        # Use optimized write path
        return optimizer.optimized_write(file_path, content)
    else:
        # Use standard write path
        return standard_write(file_path, content)

# Batch write detection
class BatchWriteDetector:
    def __init__(self):
        self.pending_writes = []
        self.batch_threshold = 3
        self.time_window = 2.0  # seconds

    def queue_write(self, file_path, content):
        """Queue write for potential batching"""
        write_op = WriteOperation(file_path, content, timestamp=time.time())
        self.pending_writes.append(write_op)

        # Check if batching is beneficial
        if self.should_batch():
            return self.execute_batch()
        else:
            return self.execute_individual(write_op)

    def should_batch(self):
        """Determine if batching would be beneficial"""
        if len(self.pending_writes) >= self.batch_threshold:
            return True

        # Check if operations are related
        if self.are_operations_related(self.pending_writes):
            return True

        return False
```

#### MultiEdit Integration

**Enhanced MultiEdit Coordination**:

```python
class OptimizedMultiEdit:
    """MultiEdit with write optimization coordination"""

    def __init__(self):
        self.write_optimizer = WriteOptimizer()

    def multi_edit_with_optimization(self, file_path, edits):
        """MultiEdit with intelligent optimization"""

        # Analyze edit complexity
        complexity = self.analyze_edit_complexity(edits)

        if complexity.should_use_template:
            # Convert to template-based rewrite
            return self.template_based_rewrite(file_path, edits)

        elif complexity.should_batch:
            # Use batched edit operations
            return self.batched_multi_edit(file_path, edits)

        else:
            # Use standard MultiEdit
            return self.standard_multi_edit(file_path, edits)

    def template_based_rewrite(self, file_path, edits):
        """Convert MultiEdit to template-based operation"""

        # Extract current file structure
        current_content = Path(file_path).read_text()
        structure = self.extract_structure(current_content)

        # Apply edits to structure
        modified_structure = self.apply_edits_to_structure(structure, edits)

        # Generate new content from template
        new_content = self.generate_from_template(modified_structure)

        # Use optimized write
        return self.write_optimizer.optimized_write(file_path, new_content)
```

#### Edit Tool Coordination

**Smart Edit Selection**:

```python
class SmartEditSelector:
    """Select optimal edit strategy based on operation characteristics"""

    def choose_edit_strategy(self, file_path, old_string, new_string):
        """Choose optimal edit approach"""

        file_size = Path(file_path).stat().st_size
        change_size = len(new_string) - len(old_string)

        # Decision matrix
        if file_size > 50000 and abs(change_size) < 100:
            # Large file, small change - use incremental
            return "incremental_edit"

        elif change_size > file_size * 0.5:
            # Major changes - use template rewrite
            return "template_rewrite"

        else:
            # Standard edit
            return "standard_edit"

    async def execute_optimized_edit(self, file_path, old_string, new_string):
        """Execute edit with optimal strategy"""

        strategy = self.choose_edit_strategy(file_path, old_string, new_string)

        if strategy == "incremental_edit":
            return await self.incremental_edit(file_path, old_string, new_string)
        elif strategy == "template_rewrite":
            return await self.template_rewrite(file_path, old_string, new_string)
        else:
            return await self.standard_edit(file_path, old_string, new_string)
```

### 3. Pre-commit Hook Integration

#### Write Optimization Pre-commit Hook

**Location**: `/Users/ryan/src/hackathon/MicrosoftHackathon2025-AgenticCoding/.claude/tools/amplihack/hooks/write_optimization.py`

```python
#!/usr/bin/env python3
"""Pre-commit hook for write operation optimization analysis"""

import sys
import json
from pathlib import Path
from datetime import datetime

def analyze_staged_files():
    """Analyze staged files for write optimization opportunities"""

    # Get staged files
    staged_files = get_staged_files()

    if not staged_files:
        return True

    # Analyze for optimization opportunities
    optimizer = WriteOptimizer()
    opportunities = optimizer.analyze_file_patterns(staged_files)

    if opportunities:
        print("🚀 Write optimization opportunities detected:")
        for opp in opportunities:
            print(f"  - {opp.description}")
            print(f"    Files: {', '.join(opp.affected_files)}")
            print(f"    Potential savings: {opp.estimated_savings}")

        # Log opportunities for future learning
        log_optimization_opportunities(opportunities)

        print("\n💡 Consider using write-optimizer agent for future similar operations")

    return True

def log_optimization_opportunities(opportunities):
    """Log opportunities for learning system"""

    log_dir = Path(".claude/runtime/logs/write_optimization")
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"opportunities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    opportunity_data = []
    for opp in opportunities:
        opportunity_data.append({
            "type": opp.type,
            "description": opp.description,
            "affected_files": opp.affected_files,
            "estimated_savings": opp.estimated_savings,
            "timestamp": datetime.now().isoformat(),
            "commit_hash": get_current_commit_hash()
        })

    log_file.write_text(json.dumps(opportunity_data, indent=2))

if __name__ == "__main__":
    success = analyze_staged_files()
    sys.exit(0 if success else 1)
```

#### Integration with Existing Hooks

**Hook Chain Enhancement**:

```python
# Enhanced hook processor
class EnhancedHookProcessor:
    """Process hooks with write optimization integration"""

    def __init__(self):
        self.write_optimizer = WriteOptimizer()
        self.existing_hooks = load_existing_hooks()

    def process_pre_commit_hooks(self):
        """Process pre-commit hooks with write optimization"""

        # Run write optimization analysis first
        optimization_results = self.write_optimizer.analyze_staged_changes()

        # Run existing hooks
        hook_results = []
        for hook in self.existing_hooks:
            result = hook.execute()
            hook_results.append(result)

        # Combine results
        return {
            "optimization_analysis": optimization_results,
            "hook_results": hook_results,
            "overall_success": all(r.success for r in hook_results)
        }
```

### 4. Agent Integration Patterns

#### Parallel Agent Coordination

**Write Optimization in Multi-Agent Workflows**:

```python
async def coordinated_agent_execution(task_requirements):
    """Execute multiple agents with write optimization coordination"""

    # Identify agents needed for task
    required_agents = identify_required_agents(task_requirements)

    # Add write optimization if beneficial
    if should_include_write_optimization(task_requirements):
        required_agents.append("write-optimizer")

    # Execute agents in parallel where possible
    agent_tasks = []
    for agent in required_agents:
        if agent == "write-optimizer":
            # Special handling for write optimizer
            task = create_write_optimization_task(task_requirements)
        else:
            task = create_standard_agent_task(agent, task_requirements)

        agent_tasks.append(task)

    # Execute with dependency resolution
    results = await execute_with_dependencies(agent_tasks)

    # Coordinate write operations from all agents
    write_operations = extract_write_operations(results)
    if write_operations:
        optimized_results = await optimize_coordinated_writes(write_operations)
        return merge_results(results, optimized_results)

    return results

def should_include_write_optimization(requirements):
    """Determine if write optimization should be included"""

    # Check for write-heavy operations
    if requirements.get("files_to_create", 0) > 2:
        return True

    if requirements.get("files_to_modify", 0) > 3:
        return True

    # Check for template opportunities
    if has_template_indicators(requirements):
        return True

    return False
```

#### Agent Communication Protocol

**Write Operation Coordination**:

```python
class WriteOperationCoordinator:
    """Coordinate write operations across multiple agents"""

    def __init__(self):
        self.pending_operations = {}
        self.agent_coordination_map = {}

    def register_agent_write_intent(self, agent_id, write_operations):
        """Register agent's intended write operations"""
        self.pending_operations[agent_id] = write_operations

        # Check for coordination opportunities
        self.identify_coordination_opportunities()

    def identify_coordination_opportunities(self):
        """Find opportunities to coordinate writes across agents"""

        # Group operations by file
        file_operations = {}
        for agent_id, operations in self.pending_operations.items():
            for op in operations:
                if op.file_path not in file_operations:
                    file_operations[op.file_path] = []
                file_operations[op.file_path].append((agent_id, op))

        # Identify conflicts and optimization opportunities
        for file_path, ops in file_operations.items():
            if len(ops) > 1:
                # Multiple agents want to write to same file
                coordination = self.resolve_file_conflicts(file_path, ops)
                self.agent_coordination_map[file_path] = coordination

    def execute_coordinated_writes(self):
        """Execute all pending writes with coordination"""

        # Execute coordinated operations first
        for file_path, coordination in self.agent_coordination_map.items():
            self.execute_coordination(coordination)

        # Execute remaining operations
        remaining_ops = self.get_remaining_operations()
        optimizer = WriteOptimizer()
        return optimizer.execute_batch(remaining_ops)
```

### 5. Performance Monitoring Integration

#### Metrics Collection

**Write Performance Tracking**:

```python
class WritePerformanceMonitor:
    """Monitor and track write operation performance"""

    def __init__(self):
        self.metrics_db = Path(".claude/runtime/metrics/write_performance.json")
        self.session_metrics = {}

    def track_write_operation(self, operation_type, file_count, duration, success):
        """Track individual write operation metrics"""

        metric = {
            "operation_type": operation_type,
            "file_count": file_count,
            "duration": duration,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "optimization_used": operation_type != "standard_write"
        }

        self.session_metrics[f"{operation_type}_{len(self.session_metrics)}"] = metric

    def generate_performance_report(self):
        """Generate performance analysis report"""

        total_operations = len(self.session_metrics)
        optimized_operations = sum(1 for m in self.session_metrics.values()
                                 if m["optimization_used"])

        total_time = sum(m["duration"] for m in self.session_metrics.values())
        optimized_time = sum(m["duration"] for m in self.session_metrics.values()
                           if m["optimization_used"])

        report = {
            "total_operations": total_operations,
            "optimized_operations": optimized_operations,
            "optimization_rate": optimized_operations / total_operations if total_operations > 0 else 0,
            "total_time": total_time,
            "average_time_per_operation": total_time / total_operations if total_operations > 0 else 0,
            "estimated_time_savings": self.calculate_time_savings(),
        }

        return report

    def update_discoveries(self, performance_gains):
        """Update DISCOVERIES.md with performance insights"""

        if performance_gains["time_savings"] > 2.0:  # Significant savings
            discovery_entry = f"""
## Write Optimization Performance Gain

**Date**: {datetime.now().strftime('%Y-%m-%d')}
**Time Savings**: {performance_gains['time_savings']:.1f} seconds
**Operations Optimized**: {performance_gains['operations_count']}
**Optimization Rate**: {performance_gains['optimization_rate']:.1%}

**Key Optimizations**:
{chr(10).join(f"- {opt}" for opt in performance_gains['optimizations_used'])}

**Impact**: {performance_gains['impact_description']}
"""

            # Append to DISCOVERIES.md
            discoveries_file = Path("DISCOVERIES.md")
            if discoveries_file.exists():
                current_content = discoveries_file.read_text()
                discoveries_file.write_text(current_content + discovery_entry)
```

### 6. Error Handling and Recovery Integration

#### Coordinated Error Recovery

**Multi-Agent Error Recovery**:

```python
class CoordinatedErrorRecovery:
    """Handle errors across multiple agents and write operations"""

    def __init__(self):
        self.operation_stack = []
        self.backup_registry = {}

    def register_operation(self, agent_id, operation):
        """Register operation for potential rollback"""

        operation_id = f"{agent_id}_{len(self.operation_stack)}"

        # Create backup if modifying existing file
        if operation.modifies_existing and Path(operation.file_path).exists():
            backup_path = self.create_backup(operation.file_path)
            self.backup_registry[operation_id] = backup_path

        self.operation_stack.append({
            "id": operation_id,
            "agent_id": agent_id,
            "operation": operation,
            "timestamp": datetime.now()
        })

    async def handle_coordinated_failure(self, failed_agent, error):
        """Handle failure with coordinated rollback"""

        # Find all operations that need rollback
        rollback_operations = []
        for op in reversed(self.operation_stack):
            rollback_operations.append(op)
            if op["agent_id"] == failed_agent:
                break

        # Execute rollback in reverse order
        for op in rollback_operations:
            await self.rollback_operation(op)

        # Clear operation stack
        self.operation_stack = self.operation_stack[:-len(rollback_operations)]

        # Notify all affected agents
        affected_agents = set(op["agent_id"] for op in rollback_operations)
        for agent in affected_agents:
            await self.notify_agent_rollback(agent, error)

    async def rollback_operation(self, operation_record):
        """Rollback individual operation"""

        op_id = operation_record["id"]
        operation = operation_record["operation"]

        if op_id in self.backup_registry:
            # Restore from backup
            backup_path = self.backup_registry[op_id]
            self.restore_from_backup(operation.file_path, backup_path)
        else:
            # Remove newly created file
            if Path(operation.file_path).exists():
                Path(operation.file_path).unlink()
```

## Performance Guarantees

### Safety Guarantees

1. **Zero Data Loss**: All write operations include backup and rollback capability
2. **Atomic Operations**: Multi-file operations complete entirely or rollback entirely
3. **Validation Integration**: All optimizations include format and syntax validation
4. **Permission Safety**: Pre-write permission and lock checking

### Performance Targets

1. **Batch Operations**: 3-5x speed improvement for related file writes
2. **Template Usage**: 60-80% time reduction for similar file structures
3. **Incremental Updates**: 75% speed improvement for small changes to large files
4. **Overall Optimization Rate**: Target 40%+ of write operations optimized

### Monitoring and Alerting

1. **Performance Degradation**: Alert if optimization actually slows operations
2. **Error Rate Monitoring**: Track and alert on optimization-related failures
3. **Rollback Success Rate**: Monitor and ensure 100% successful rollback capability
4. **Learning Effectiveness**: Track pattern recognition and template reuse rates

## Implementation Roadmap

### Phase 1: Core Integration (Week 1)

- [ ] Implement write-optimizer agent
- [ ] Create WRITE_PATTERNS.md documentation
- [ ] Add basic tool coordination (Write/MultiEdit/Edit)
- [ ] Implement performance monitoring

### Phase 2: Workflow Integration (Week 2)

- [ ] Integrate with Step 4, 5, 6 of workflow
- [ ] Add pre-commit hook integration
- [ ] Implement agent coordination protocols
- [ ] Add error recovery systems

### Phase 3: Advanced Optimization (Week 3)

- [ ] Implement template extraction and reuse
- [ ] Add dependency-aware write ordering
- [ ] Create learning and adaptation systems
- [ ] Optimize cloud sync handling

### Phase 4: Performance Optimization (Week 4)

- [ ] Fine-tune optimization thresholds
- [ ] Implement advanced batching strategies
- [ ] Add comprehensive performance analytics
- [ ] Create automated optimization suggestions

## Success Metrics

1. **Time Savings**: >50% reduction in write operation time for optimizable operations
2. **Error Reduction**: <2% increase in write-related errors
3. **Adoption Rate**: >60% of write operations use optimization when beneficial
4. **User Satisfaction**: Transparent operation with clear performance benefits
5. **Learning Effectiveness**: Continuous improvement in optimization selection

Remember: The integration should be transparent to users while providing significant performance benefits and maintaining the highest levels of data safety and operation reliability.
