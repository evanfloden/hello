#!/usr/bin/env nextflow

params.batch_size = 2
params.delay = 0.5
params.greeting_style = 'uppercase'
params.repeat_count = 1
params.outdir = 'results'

process sayHello {
    conda 'conda-forge::python=3.11 conda-forge::procps-ng=4.0'
    publishDir "${params.outdir}", mode: 'copy'

    input:
    val greetings

    output:
    path 'greetings_*.txt'
    path 'metrics_*.json'

    script:
    def style = params.greeting_style
    def repeat = params.repeat_count
    def delay = params.delay
    def task_id = task.index
    """
    #!/usr/bin/env python3
    import time
    import json

    greetings = "${greetings}".split(',')
    style = "${style}"
    repeat = ${repeat}
    delay = ${delay}

    start_time = time.time()
    results = []

    for greeting in greetings:
        time.sleep(delay)

        if style == 'uppercase':
            output = greeting.upper()
        elif style == 'lowercase':
            output = greeting.lower()
        elif style == 'titlecase':
            output = greeting.title()
        else:
            output = greeting

        for i in range(repeat):
            results.append(f"{output} world!")

    elapsed = time.time() - start_time

    # Write greetings
    with open('greetings_${task_id}.txt', 'w') as f:
        f.write('\\n'.join(results))

    # Write metrics
    metrics = {
        'greetings_processed': len(greetings) * repeat,
        'elapsed_seconds': elapsed,
        'throughput': (len(greetings) * repeat) / elapsed if elapsed > 0 else 0,
        'efficiency_score': (len(greetings) * repeat) / (elapsed * delay) if elapsed > 0 else 0
    }

    with open('metrics_${task_id}.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    """
}

process aggregateMetrics {
    conda 'conda-forge::python=3.11 conda-forge::procps-ng=4.0'
    publishDir "${params.outdir}", mode: 'copy'

    input:
    path metrics_files

    output:
    path 'final_metrics.json'

    script:
    """
    #!/usr/bin/env python3
    import json
    import glob

    all_metrics = []
    for f in glob.glob('metrics_*.json'):
        with open(f) as fp:
            all_metrics.append(json.load(fp))

    total_greetings = sum(m['greetings_processed'] for m in all_metrics)
    total_time = sum(m['elapsed_seconds'] for m in all_metrics)
    avg_throughput = sum(m['throughput'] for m in all_metrics) / len(all_metrics)
    avg_efficiency = sum(m['efficiency_score'] for m in all_metrics) / len(all_metrics)

    final_metrics = {
        'total_greetings_processed': total_greetings,
        'total_elapsed_seconds': total_time,
        'average_throughput': avg_throughput,
        'average_efficiency_score': avg_efficiency,
        'target_metric': avg_efficiency  # This is what we'll optimize
    }

    with open('final_metrics.json', 'w') as f:
        json.dump(final_metrics, f, indent=2)

    print(f"Final Efficiency Score: {avg_efficiency:.4f}")
    """
}

workflow {
    greetings_ch = channel.of('Bonjour', 'Ciao', 'Hello', 'Hola', 'Namaste', 'Salaam')
        .buffer(size: params.batch_size)
        .map { items -> items.join(',') }

    sayHello(greetings_ch)

    metrics_ch = sayHello.out[1].collect()

    aggregateMetrics(metrics_ch)
}
