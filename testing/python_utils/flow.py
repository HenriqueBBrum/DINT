## Used by receive.py to save Flow specific information
import constants



class Flow:
  def __init__(self, flow_id, throughput, first_pdp_timestamp, lastest_pdp_timestamp, experiment_type):
    self.flow_id = flow_id
    self.avg_throughput = throughput
    self.first_pdp_timestamp = first_pdp_timestamp
    self.lastest_pdp_timestamp = lastest_pdp_timestamp

    self.is_anomalous_now = False
    self.was_anomalous = False
    self.anomalous_identification_timestamp = []

    self.experiment_type = experiment_type


    self.check_anomalous()


  def __str__(self):
    return f"Flow {self.flow_id}, Avg. throughput: {self.avg_throughput}, Time Active: {self.lastest_pdp_timestamp - self.first_pdp_timestamp}"+"\n"


  def update_same_flow(self, throughput, lastest_pdp_timestamp):
    self.avg_throughput = (self.avg_throughput + throughput)/2
    self.lastest_pdp_timestamp = lastest_pdp_timestamp

    self.check_anomalous()



  def same_id_but_different_flow(self, new_throughput, new_first_pdp_timestamp, new_lastest_pdp_timestamp):
    self.avg_throughput = new_throughput
    self.first_pdp_timestamp = new_first_pdp_timestamp
    self.lastest_pdp_timestamp = new_lastest_pdp_timestamp

    self.check_anomalous()



  def check_anomalous(self):
    throughput_threshold, duration_threshold = 0, 0
    if(self.experiment_type == "elephant_mice"):
        throughput_threshold=constants.ELEPHANT_FLOW_THROUGHPUT_THRESHOLD
        duration_threshold=constants.ELEPHANT_FLOW_TIME_THRESHOLD
    else:
        throughput_threshold=constants.MICROBURST_FLOW_THROUGHPUT_THRESHOLD
        duration_threshold=constants.MICROBURST_FLOW_TIME_THRESHOLD


    if(self.is_anomalous_now is False and self.avg_throughput >= throughput_threshold and 
        self.lastest_pdp_timestamp - self.first_pdp_timestamp >= duration_threshold*constants.MICROSEG):
            self.is_anomalous_now = True
            self.was_anomalous = True
            self.anomalous_identification_timestamp.append((self.first_pdp_timestamp, self.lastest_pdp_timestamp))
    elif(self.is_anomalous_now is True and self.avg_throughput < throughput_threshold):
        print("heyyyyyy")
        self.is_anomalous_now = False
        self.anomalous_identification_timestamp[-1][1] = self.lastest_pdp_timestamp
        