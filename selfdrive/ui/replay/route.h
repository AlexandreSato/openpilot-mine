#pragma once

#include <QDir>
#include <QThread>

#include "selfdrive/common/util.h"
#include "selfdrive/ui/replay/framereader.h"
#include "selfdrive/ui/replay/logreader.h"

const QDir CACHE_DIR(util::getenv("COMMA_CACHE", "/tmp/comma_download_cache/").c_str());

struct RouteIdentifier {
  QString dongle_id;
  QString timestamp;
  int segment_id;
  QString str;
};

struct SegmentFile {
  QString rlog;
  QString qlog;
  QString road_cam;
  QString driver_cam;
  QString wide_road_cam;
  QString qcamera;
};

class Route {
public:
  Route(const QString &route, const QString &data_dir = {});
  bool load();
  inline const QString &name() const { return route_.str; }
  inline const RouteIdentifier &identifier() const { return route_; }
  inline const std::map<int, SegmentFile> &segments() const { return segments_; }
  inline const SegmentFile &at(int n) { return segments_.at(n); }
  static RouteIdentifier parseRoute(const QString &str);

protected:
  bool loadFromLocal();
  bool loadFromServer();
  bool loadFromJson(const QString &json);
  void addFileToSegment(int seg_num, const QString &file);
  RouteIdentifier route_ = {};
  QString data_dir_;
  std::map<int, SegmentFile> segments_;
};

class Segment : public QObject {
  Q_OBJECT

public:
  Segment(int n, const SegmentFile &files, bool load_dcam, bool load_ecam);
  ~Segment();
  inline bool isLoaded() const { return !loading_ && success_; }

  const int seg_num = 0;
  std::unique_ptr<LogReader> log;
  std::unique_ptr<FrameReader> frames[MAX_CAMERAS] = {};

signals:
  void loadFinished(bool success);

protected:
  void loadFile(int id, const std::string file);
  bool downloadFile(int id, const std::string &url, const std::string local_file);
  std::string cacheFilePath(const std::string &file);

  std::atomic<bool> success_ = true, aborting_ = false;
  std::atomic<int> loading_ = 0;
  std::vector<QThread*> loading_threads_;
  const int max_retries_ = 3;
};
