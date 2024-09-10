import matplotlib.pyplot as plt
import pandas as pd

#==============================================================================
# Plot TTLs
#==============================================================================

def get_square_wave(df): 

    # Create a new DataFrame with repeated elements
    square_wave = {'timestamp': df['timestamp'].repeat(2).tolist()[1:],
        'state': df['state'].repeat(2).tolist()[:-1]
        }
    square_wave = pd.DataFrame(square_wave)
    return square_wave


def plot_ttl_trace(ttl_state_df, *, t_start, t_end):

    fig, ax = plt.subplots(figsize=(12, 6))  # Set the figure size (width, height) in inches
    ttl_pulse = get_square_wave(ttl_state_df)
    ttl_pulse.plot(x='timestamp', y='state', linewidth=0.5, ax=ax)
    ax.set_xlabel('timestamp (s)')
    ax.legend(loc='upper right')
    ax.set_xlim(t_start, t_end)

    plt.show()

    return fig, ax