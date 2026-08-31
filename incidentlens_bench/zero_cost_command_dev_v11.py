#!/usr/bin/env python3
# Scoring-only correction for DEV v1. The adapter, prompt, model, task split,
# and selection logic remain exactly the same. CyBashBench MCQ canonical text
# is stored in dataset_task_metadata['bash_command']; correct_answer stores the
# option letter and must not be used as the text reference.
import zero_cost_command_dev as dev

def corrected_ref_answer(meta):
    return str(meta.get('bash_command',''))

dev.ref_answer = corrected_ref_answer

if __name__ == '__main__':
    dev.main()
