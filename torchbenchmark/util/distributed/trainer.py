import os

import torch.distributed as dist


class Trainer():
    def __init__(self, args, model_class, mode="SPMD"):
        self.args = args
        self.model_class = model_class
        self.mode = mode

    def setup(self):
        if self.mode == "SPMD":
            local_rank = int(os.getenv("LOCAL_RANK", -1))
            self.local_rank = local_rank
            # set the visible devices so that each SPMD process only sees one
            # CUDA device
            # N.B.: this has to be done before using any CUDA API from torch
            # N.B.: Remove the following block as HF Accelerator by default puts
            # the model to the device corresponding to LOCAL_RANK
            """
            os.environ["CUDA_VISIBLE_DEVICES"] = f"{local_rank}"
            assert torch.cuda.device_count() == 1, (
                "SPMD Trainer expects 1 visible device per process, but saw "
                f"{torch.cuda.device_count()} devices."
            )
            """

            world_size = int(os.getenv("WORLD_SIZE", -1))
            rank = int(os.getenv("RANK", -1))

            assert local_rank != -1 and world_size != -1 and rank != -1, (
                "Failed to retrieve SPMD configurations from environment "
                f"variables. local_rank={local_rank}, world_size={world_size}, "
                f"rank={rank}."

            )

            # TODO: hardcode NCCL for now, make this configurable if necessary
            print("====== init pg")
            dist.init_process_group("nccl", init_method=self.args.dist_url, rank=rank, world_size=world_size)
        else:
            raise ValueError(f"Unrecognized distributed training mode {self.mode}")

    def teardown(self):
        if self.mode == "SPMD":
            dist.destroy_process_group()
