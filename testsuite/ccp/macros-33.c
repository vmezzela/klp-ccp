#define __cold __attribute__((__cold__))
#define __latent_entropy
#define __init __cold __latent_entropy

static int __init pu_f(void)
{
	return 0;
}
