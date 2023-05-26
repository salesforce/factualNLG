import matplotlib.gridspec as gridspec, matplotlib.pyplot as plt
from collections import Counter
import json

def load_reasoning_counts(fn, anno_key="annotation_nina"):
    with open(fn, "r") as f:
        annotated_reasons = json.load(f)

    model_counts = {}
    for d in annotated_reasons:
        for s in d["samples"]:
            if anno_key not in s:
                continue
            model_name = s["model"].replace("llama", "LLaMa").replace("claudev13", "Claude-v1.3").replace("gpt", "GPT")
            if model_name == "cgpt":
                model_name = "GPT3.5-turbo"
            if model_name not in model_counts:
                model_counts[model_name] = Counter()
            
            model_counts[model_name][s[anno_key]] += 1
    return model_counts

def draw_reason_histogram(model_counts, resort=True, cleanup_names=True, plot_title=None, print_perc=True, legend_x=-0.2, save_to_file=None, plot_legend=True):
    likert_vals = ["correct", "partially_correct", "no_explanation", "unrelated", "incorrect"]
    legend_vals = ["Correct", "Partially correct", "No expl.", "Unrelated", "Incorrect"]
    colors = ["#87a0cf", "#ccdefa", "#dedede", "#f2d6d5", "#d99493"]

    explainers = model_counts.keys()
    all_label_counts = model_counts

    if resort:
        explainers = sorted(explainers, key=lambda e: (all_label_counts[e]["correct"] ) / sum(all_label_counts[e].values()), reverse=True)

    figure_height = 0.42 * len(explainers) + (0.7 if plot_title is not None else 0.0) + 0.5 # Last bit for the legend
    fig, axs = plt.subplots(len(explainers), 1, figsize=(10, figure_height), sharex=False) # , sharey=True
    gs1 = gridspec.GridSpec(len(explainers), 1)
    gs1.update(wspace=0.0, hspace=0.0) # set the spacing between axes.

    for i, explainer in enumerate(explainers):
        ax = plt.subplot(gs1[i])
        label_counts = all_label_counts[explainer]
        label_counts_arr = [label_counts[l] for l in likert_vals]
        label_counts_arr[2] += label_counts["other"]

        current_x = 0
        for j, v in enumerate(label_counts_arr):
            ax.barh(0, v, left=current_x, color=colors[j], height=1.0)
            current_x += v
            if v > 0:
                perc = 100.0 * v / sum(model_counts[explainer].values())
                txt = "%.0f" % (perc) if print_perc else "%d" % (v)
                if txt == "0":
                    continue
                ax.text(current_x - v/2, -0.15, txt, color='black', ha='center', fontsize=20) # , fontweight='bold'
        
        model_name = explainer.replace("output_", "").replace("_short", "")
        if cleanup_names:
            model_name = model_name.replace("gpt", "GPT")
            if model_name.lower() == "cgpt":
                model_name = "GPT3.5-turbo"
            elif model_name == "llama-13b":
                model_name = "LLaMa-13B"
            else:
                model_name = model_name.capitalize()
            
            
        ax.text(legend_x, 0.4, model_name, fontsize=16, transform=ax.transAxes)
        # set xrange
        ax.set_xlim([0, sum(label_counts_arr)])
        ax.set_xticks([])
        ax.set_yticks([])
        ax.axis('off')
    if plot_legend:
        # If we save to file, for now, 
        fig.legend(legend_vals, loc='right', ncol=5, bbox_to_anchor=(1.00, -0.02), fontsize=15)
    fig.subplots_adjust(wspace=0, hspace=0)
    if plot_title is not None:
        plt.suptitle(plot_title, fontsize=20)

    plt.tight_layout()
    fig.patch.set_facecolor('white')
    if save_to_file:
        plt.savefig(save_to_file, dpi=300)
    plt.show()
